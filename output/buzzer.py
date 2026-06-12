"""
output/buzzer.py
팀원 4 담당: 3V 능동 부저 출력 제어

핀 번호는 반드시 BCM GPIO 번호 기준입니다.
- 3V 능동 부저: GPIO24

주의
- 3V 능동 부저는 주파수 제어가 아니라 ON/OFF 패턴으로 소리를 냅니다.
- 이 파일은 오류가 발생해도 전체 프로그램이 멈추지 않도록 작성되어 있습니다.
"""

from __future__ import annotations

import logging
import time
from typing import Iterable, Optional, Tuple

logger = logging.getLogger(__name__)

# ============================================================
# 팀원 4 부저 핀 번호 명시
# 기준: BCM GPIO 번호
# 실제 연결:
#   3V 능동 부저 + 또는 Signal -> GPIO24
#   3V 능동 부저 - 또는 GND    -> GND
# ============================================================
BUZZER_PIN = 24  # 3V 능동 부저 연결 핀: GPIO24

# 한눈에 확인하기 위한 한국어 핀맵
BUZZER_PINMAP_KR = {
    "3V 능동 부저": "GPIO24",
}


class BuzzerController:
    """3V 능동 부저를 안전하게 제어하는 클래스."""

    def __init__(self) -> None:
        self.buzzer: Optional[object] = None  # 3V 능동 부저, GPIO24
        self.available = False
        self._setup()

    def _setup(self) -> None:
        """GPIO Buzzer 객체 초기화. 실패해도 예외를 밖으로 던지지 않습니다."""
        try:
            from gpiozero import Buzzer
        except Exception as exc:
            logger.warning("GPIO Zero를 불러오지 못했습니다. 부저 기능을 비활성화합니다: %s", exc)
            return

        try:
            # 여기서 BUZZER_PIN=24는 BCM GPIO 번호입니다.
            self.buzzer = Buzzer(BUZZER_PIN, initial_value=False)
            self.available = True
            logger.info("부저 초기화 완료: GPIO%d", BUZZER_PIN)
        except Exception as exc:
            self.buzzer = None
            logger.warning("부저(GPIO%d) 초기화 실패: %s", BUZZER_PIN, exc)

    def _beep_once(self, duration: float) -> bool:
        """duration초 동안 부저(GPIO24)를 한 번 울림."""
        if self.buzzer is None:
            logger.warning("부저(GPIO24)를 사용할 수 없습니다.")
            return False

        try:
            self.buzzer.on()
            time.sleep(max(0.0, duration))
            return True
        except Exception as exc:
            logger.warning("부저(GPIO24) 울림 실패: %s", exc)
            return False
        finally:
            try:
                self.buzzer.off()
            except Exception as exc:
                logger.warning("부저(GPIO24) 끄기 실패: %s", exc)

    def beep_pattern(self, pattern: Iterable[Tuple[float, float]]) -> bool:
        """
        여러 번의 비프 패턴 실행.

        사용 핀:
            3V 능동 부저 -> GPIO24

        pattern 형식:
            [(울리는 시간, 쉬는 시간), ...]
        """
        success = True
        for duration, pause in pattern:
            if not self._beep_once(duration):
                success = False
            time.sleep(max(0.0, pause))
        return success

    def short_beep(self) -> bool:
        """짧은 비프음: 부저(GPIO24)로 삐."""
        return self._beep_once(0.12)

    def success_sound(self) -> bool:
        """성공음: 부저(GPIO24)로 짧게 두 번, 삐삐."""
        return self.beep_pattern([
            (0.10, 0.08),
            (0.10, 0.00),
        ])

    def error_sound(self) -> bool:
        """오류음: 부저(GPIO24)로 비교적 길게 세 번, 삐-삐-삐."""
        return self.beep_pattern([
            (0.22, 0.10),
            (0.22, 0.10),
            (0.22, 0.00),
        ])

    def off(self) -> bool:
        """부저(GPIO24) 끄기."""
        if self.buzzer is None:
            return False

        try:
            self.buzzer.off()
            return True
        except Exception as exc:
            logger.warning("부저(GPIO24) 끄기 실패: %s", exc)
            return False

    def cleanup(self) -> bool:
        """프로그램 종료 전 부저 정리."""
        success = self.off()
        if self.buzzer is None:
            return success

        try:
            self.buzzer.close()
            return success
        except Exception as exc:
            logger.warning("부저(GPIO24) 정리 실패: %s", exc)
            return False


_controller: Optional[BuzzerController] = None


def get_controller() -> BuzzerController:
    """BuzzerController 싱글턴 반환. 실제 GPIO 초기화는 처음 사용할 때 수행됩니다."""
    global _controller
    if _controller is None:
        _controller = BuzzerController()
    return _controller


# 아래 함수들은 main.py에서 바로 import해서 쓰기 쉽게 만든 함수입니다.
def short_beep() -> bool:
    return get_controller().short_beep()


def success_sound() -> bool:
    return get_controller().success_sound()


def error_sound() -> bool:
    return get_controller().error_sound()


def buzzer_off() -> bool:
    return get_controller().off()


def cleanup() -> bool:
    return get_controller().cleanup()
