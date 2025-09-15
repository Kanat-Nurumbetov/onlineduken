from appium.webdriver.common.appiumby import AppiumBy as By
from screens.base_screen import BaseScreen


class ScannerScreen(BaseScreen):
    GALLERY_BTN_ID = "kz.halyk.onlinebank.stage:id/gallery_button"

    def tap_upload_from_gallery(self):
        gallery_locator = (By.ID, self.GALLERY_BTN_ID)
        self.click_element(gallery_locator)
