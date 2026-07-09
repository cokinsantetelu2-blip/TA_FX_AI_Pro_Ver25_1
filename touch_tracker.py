# touch_tracker.py
# TA FX AI Pro Ver25.1
# Fibonacci Touch Tracker
# 通貨別・BUY/SELL別・保存対応版
# Ver25.1 監査ログ強化版
#
# 目的:
# ・0本へ戻る原因を update_touch_state() 内で特定する
# ・修正ではなく監査のみ
#
# 維持内容
# ・初回タッチは必ず0本
# ・タッチ中はtouch_indexを上書きしない
# ・フィボ範囲外に出たら in_touch_area=False
# ・再タッチした時だけ新規0本として記録
# ・6本以上は期限切れ
# ・touch_state.json 保存は維持

import json
import os


class TouchTracker:

    def __init__(self, save_file="touch_state.json"):
        self.save_file = save_file
        self.touches = {}
        self.load()

    def reset(self):
        self.touches = {}
        self.save()

    def load(self):
        if not os.path.exists(self.save_file):
            self.touches = {}
            return

        try:
            with open(self.save_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                self.touches = data
            else:
                self.touches = {}

        except Exception:
            self.touches = {}

    def save(self):
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(self.touches, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("TouchTracker保存エラー:", e)

    def _normalize_symbol(self, symbol):
        if symbol is None:
            return "UNKNOWN"
        return str(symbol).upper()

    def _normalize_side(self, side):
        if side is None:
            return "UNKNOWN"
        return str(side).upper()

    def _safe_int(self, value):
        try:
            return int(value)
        except Exception:
            return None

    def _ensure_symbol_side(self, symbol, side):
        symbol = self._normalize_symbol(symbol)
        side = self._normalize_side(side)

        if symbol not in self.touches:
            self.touches[symbol] = {}

        if side not in self.touches[symbol]:
            self.touches[symbol][side] = {
                "touch_index": None,
                "touch_side": side,
                "touch_level": None,
                "in_touch_area": False,
            }

        return symbol, side

    def _audit_data(self, title, symbol, side, current_index, is_touching, level, data, max_bars):
        touch_index = data.get("touch_index")
        touch_level = data.get("touch_level")
        in_touch_area = data.get("in_touch_area", False)

        bars = None
        current_i = self._safe_int(current_index)
        touch_i = self._safe_int(touch_index)

        if current_i is not None and touch_i is not None:
            bars = current_i - touch_i

        print("")
        print("========== TOUCH TRACKER UPDATE AUDIT ==========")
        print("TITLE:", title)
        print("symbol:", symbol)
        print("side:", side)
        print("current_index:", current_index)
        print("is_touching:", is_touching)
        print("incoming_level:", level)
        print("saved_touch_index:", touch_index)
        print("saved_touch_level:", touch_level)
        print("saved_in_touch_area:", in_touch_area)
        print("bars_from_saved_touch:", bars)
        print("max_bars:", max_bars)
        print("raw_data:", data)
        print("================================================")
        print("")

    def update_touch_state(
        self,
        candle_index,
        side,
        is_touching,
        level=None,
        symbol=None,
        max_bars=5
    ):
        symbol, side = self._ensure_symbol_side(symbol, side)
        data = self.touches[symbol][side]

        current_index = self._safe_int(candle_index)

        self._audit_data(
            title="BEFORE UPDATE",
            symbol=symbol,
            side=side,
            current_index=current_index,
            is_touching=is_touching,
            level=level,
            data=data,
            max_bars=max_bars,
        )

        if current_index is None:
            print("[TouchDecision] current_index が None のため更新しない")
            return self.get_status(
                current_index=candle_index,
                side=side,
                symbol=symbol,
                max_bars=max_bars
            )

        # フィボ範囲外
        if not is_touching:
            if data.get("in_touch_area", False):
                print("[TouchDecision] フィボ範囲外へ出たため in_touch_area=False に変更")
                data["in_touch_area"] = False
                self.save()
            else:
                print("[TouchDecision] フィボ範囲外。すでに in_touch_area=False のため変更なし")

            self._audit_data(
                title="AFTER UPDATE / NOT TOUCHING",
                symbol=symbol,
                side=side,
                current_index=current_index,
                is_touching=is_touching,
                level=level,
                data=data,
                max_bars=max_bars,
            )

            return self.get_status(
                current_index=current_index,
                side=side,
                symbol=symbol,
                max_bars=max_bars
            )

        # フィボ範囲内にいるが、すでにタッチ中なら上書きしない
        if is_touching and data.get("in_touch_area", False):
            print("[TouchDecision] タッチ中継続。touch_index は上書きしない")
            print("[TouchDecision] 0本リセットなし")

            self._audit_data(
                title="AFTER UPDATE / STILL TOUCHING",
                symbol=symbol,
                side=side,
                current_index=current_index,
                is_touching=is_touching,
                level=level,
                data=data,
                max_bars=max_bars,
            )

            return self.get_status(
                current_index=current_index,
                side=side,
                symbol=symbol,
                max_bars=max_bars
            )

        # 初回タッチ、または一度範囲外に出た後の再タッチ
        print("[TouchDecision] 新規タッチとして記録")
        print("[TouchDecision] 理由: is_touching=True かつ in_touch_area=False")
        print("[TouchDecision] ここで touch_index=current_index になり 0本スタート")

        data["touch_index"] = current_index
        data["touch_side"] = side
        data["touch_level"] = level
        data["in_touch_area"] = True

        self.save()

        self._audit_data(
            title="AFTER UPDATE / NEW TOUCH RESET TO 0",
            symbol=symbol,
            side=side,
            current_index=current_index,
            is_touching=is_touching,
            level=level,
            data=data,
            max_bars=max_bars,
        )

        return self.get_status(
            current_index=current_index,
            side=side,
            symbol=symbol,
            max_bars=max_bars
        )

    def record_touch(self, candle_index, side, level, symbol=None, max_bars=5):
        return self.update_touch_state(
            candle_index=candle_index,
            side=side,
            is_touching=True,
            level=level,
            symbol=symbol,
            max_bars=max_bars
        )

    def release_touch(self, candle_index, side, symbol=None, max_bars=5):
        return self.update_touch_state(
            candle_index=candle_index,
            side=side,
            is_touching=False,
            level=None,
            symbol=symbol,
            max_bars=max_bars
        )

    def has_touch(self, side=None, symbol=None):
        symbol = self._normalize_symbol(symbol)

        if symbol not in self.touches:
            return False

        if side is None:
            for side_data in self.touches[symbol].values():
                if side_data.get("touch_index") is not None:
                    return True
            return False

        side = self._normalize_side(side)

        if side not in self.touches[symbol]:
            return False

        return self.touches[symbol][side].get("touch_index") is not None

    def bars_since_touch(self, current_index, side=None, symbol=None):
        symbol = self._normalize_symbol(symbol)

        if symbol not in self.touches:
            return None

        if side is None:
            return None

        side = self._normalize_side(side)

        if side not in self.touches[symbol]:
            return None

        touch_index = self.touches[symbol][side].get("touch_index")

        current_index = self._safe_int(current_index)
        touch_index = self._safe_int(touch_index)

        if current_index is None or touch_index is None:
            return None

        bars = current_index - touch_index

        if bars < 0:
            return None

        return bars

    def is_valid(self, current_index, side=None, symbol=None, max_bars=5):
        bars = self.bars_since_touch(
            current_index=current_index,
            side=side,
            symbol=symbol
        )

        if bars is None:
            return False

        return 0 <= bars <= max_bars

    def get_status(self, current_index, side=None, symbol=None, max_bars=5):
        symbol = self._normalize_symbol(symbol)
        side = self._normalize_side(side)

        touch_index = None
        touch_level = None
        in_touch_area = False

        if symbol in self.touches and side in self.touches[symbol]:
            data = self.touches[symbol][side]
            touch_index = data.get("touch_index")
            touch_level = data.get("touch_level")
            in_touch_area = data.get("in_touch_area", False)

        if not self.has_touch(side=side, symbol=symbol):
            return {
                "valid": False,
                "expired": False,
                "bars": None,
                "touch_index": touch_index,
                "side": side,
                "level": touch_level,
                "in_touch_area": in_touch_area,
                "text": "フィボタッチなし",
                "display_text": "フィボタッチなし"
            }

        bars = self.bars_since_touch(
            current_index=current_index,
            side=side,
            symbol=symbol
        )

        valid = self.is_valid(
            current_index=current_index,
            side=side,
            symbol=symbol,
            max_bars=max_bars
        )

        expired = False
        if bars is not None and bars > max_bars:
            expired = True

        if bars is None:
            display_text = "フィボタッチなし"
        elif valid:
            display_text = f"{bars}本経過 / {max_bars}本以内"
        else:
            display_text = f"{bars}本経過 / 期限切れ"

        return {
            "valid": valid,
            "expired": expired,
            "bars": bars,
            "touch_index": touch_index,
            "side": side,
            "level": touch_level,
            "in_touch_area": in_touch_area,
            "text": display_text,
            "display_text": display_text
        }


def create_touch_tracker():
    return TouchTracker()