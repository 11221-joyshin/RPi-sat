"""
output/led.py
팀원 4 담당: LED 출력 제어

핀 번호는 반드시 BCM GPIO 번호 기준입니다.
- 빨강 LED: GPIO17
- 초록 LED: GPIO27
- 노랑 LED: GPIO22
- 파랑 LED: GPIO23

주의
- 이 파일은 오류가 발생해도 전체 프로그램이 멈추지 않도록 작성되어 있습니다.
- GPIO Zero를 사용합니다.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ============================================================
# 팀원 4 LED 핀 번호 명시
# 기준: BCM GPIO 번호
# 실제 연결:
#   빨강 LED  -> GPIO17
#   초록 LED  -> GPIO27
#   노랑 LED  -> GPIO22
#   파랑 LED  -> GPIO23
# ============================================================
RED_LED_PIN = 17      # 빨강 LED 연결 핀: GPIO17
GREEN_LED_PIN = 27    # 초록 LED 연결 핀: GPIO27
YELLOW_LED_PIN = 22   # 노랑 LED 연결 핀: GPIO22
BLUE_LED_PIN = 23     # 파랑 LED 연결 핀: GPIO23

# 색상 이름과 실제 GPIO 핀 번호 매핑
LED_PINS = {
    "red": RED_LED_PIN,        # red LED    -> GPIO17
    "green": GREEN_LED_PIN,    # green LED  -> GPIO27
    "yellow": YELLOW_LED_PIN,  # yellow LED -> GPIO22
    "blue": BLUE_LED_PIN,      # blue LED   -> GPIO23
}

# 한눈에 확인하기 위한 한국어 핀맵
LED_PINMAP_KR = {
    "빨강 LED": "GPIO17",
    "초록 LED": "GPIO27",
    "노랑 LED": "GPIO22",
    "파랑 LED": "GPIO23",
}

# 한국어 별칭도 허용
COLOR_ALIASES = {
    "빨강": "red",
    "빨간색": "red",
    "red": "red",
    "r": "red",
    "초록": "green",
    "초록색": "green",
    "green": "green",
    "g": "green",
    "노랑": "yellow",
    "노란색": "yellow",
    "yellow": "yellow",
    "y": "yellow",
    "파랑": "blue",
    "파란색": "blue",
    "blue": "blue",
    "b": "blue",
}


class LEDController:
    """LED 4개를 안전하게 제어하는 클래스."""

    def __init__(self) -> None:
        self.leds: Dict[str, Optional[object]] = {
            "red": None,      # 빨강 LED, GPIO17
            "green": None,    # 초록 LED, GPIO27
            "yellow": None,   # 노랑 LED, GPIO22
            "blue": None,     # 파랑 LED, GPIO23
        }
        self.available = False
        self._setup()

    def _setup(self) -> None:
        """GPIO LED 객체 초기화. 실패해도 예외를 밖으로 던지지 않습니다."""
        try:
            from gpiozero import LED
        except Exception as exc:
            logger.warning("GPIO Zero를 불러오지 못했습니다. LED 기능을 비활성화합니다: %s", exc)
            return

        for color, pin in LED_PINS.items():
            try:
                # 여기서 pin 값은 BCM GPIO 번호입니다.
                # red=17, green=27, yellow=22, blue=23
                self.leds[color] = LED(pin, initial_value=False)
                self.available = True
                logger.info("%s LED 초기화 완료: GPIO%d", color, pin)
            except Exception as exc:
                self.leds[color] = None
                logger.warning("%s LED(GPIO%d) 초기화 실패: %s", color, pin, exc)

    @staticmethod
    def _normalize_color(color: str) -> Optional[str]:
        if color is None:
            return None
        return COLOR_ALIASES.get(str(color).strip().lower())

    def all_off(self) -> bool:
        """모든 LED 끄기: GPIO17, GPIO27, GPIO22, GPIO23 모두 OFF."""
        success = True
        for color, led in self.leds.items():
            if led is None:
                continue
            try:
                led.off()
            except Exception as exc:
                success = False
                logger.warning("%s LED 끄기 실패: %s", color, exc)
        return success

    def on(self, color: str) -> bool:
        """
        특정 LED만 켜기.

        색상별 핀 번호:
            red    -> GPIO17
            green  -> GPIO27
            yellow -> GPIO22
            blue   -> GPIO23

        사용 예:
            on("red")
            on("초록")
        """
        normalized = self._normalize_color(color)
        if normalized not in self.leds:
            logger.warning("알 수 없는 LED 색상: %s", color)
            return False

        self.all_off()

        led = self.leds.get(normalized)
        pin = LED_PINS.get(normalized)
        if led is None:
            logger.warning("%s LED(GPIO%s)를 사용할 수 없습니다.", normalized, pin)
            return False

        try:
            led.on()
            logger.info("%s LED 켜짐: GPIO%d", normalized, pin)
            return True
        except Exception as exc:
            logger.warning("%s LED(GPIO%d) 켜기 실패: %s", normalized, pin, exc)
            return False

    def success(self) -> bool:
        """성공 상태 표시: 초록 LED(GPIO27) 켜기."""
        return self.on("green")

    def error(self) -> bool:
        """오류 상태 표시: 빨강 LED(GPIO17) 켜기."""
        return self.on("red")

    def waiting(self) -> bool:
        """대기 상태 표시: 노랑 LED(GPIO22) 점멸."""
        self.all_off()

        yellow = self.leds.get("yellow")
        if yellow is None:
            logger.warning("노랑 LED(GPIO22)를 사용할 수 없습니다.")
            return False

        try:
            yellow.blink(on_time=0.5, off_time=0.5, background=True)
            logger.info("대기 상태 표시: 노랑 LED(GPIO22) 점멸")
            return True
        except Exception as exc:
            logger.warning("대기 상태 표시 실패, 노랑 LED(GPIO22): %s", exc)
            return False

    def working(self) -> bool:
        """작업 중 상태 표시: 파랑 LED(GPIO23) 켜기."""
        return self.on("blue")

    def cleanup(self) -> bool:
        """프로그램 종료 전 LED 정리."""
        success = self.all_off()
        for color, led in self.leds.items():
            if led is None:
                continue
            try:
                led.close()
            except Exception as exc:
                success = False
                logger.warning("%s LED 정리 실패: %s", color, exc)
        return success


_controller: Optional[LEDController] = None


def get_controller() -> LEDController:
    """LEDController 싱글턴 반환. 실제 GPIO 초기화는 처음 사용할 때 수행됩니다."""
    global _controller
    if _controller is None:
        _controller = LEDController()
    return _controller


# 아래 함수들은 main.py에서 바로 import해서 쓰기 쉽게 만든 함수입니다.
def all_leds_off() -> bool:
    return get_controller().all_off()


def led_on(color: str) -> bool:
    return get_controller().on(color)


def show_success() -> bool:
    return get_controller().success()


def show_error() -> bool:
    return get_controller().error()


def show_waiting() -> bool:
    return get_controller().waiting()


def show_working() -> bool:
    return get_controller().working()


def cleanup() -> bool:
    return get_controller().cleanup()
