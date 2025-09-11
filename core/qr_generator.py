# core/qr_gen.py
from pathlib import Path
import os, random
from urllib.parse import quote
from dotenv import load_dotenv
import qrcode
from qrcode.constants import ERROR_CORRECT_M

class QrGenerator:
    def __init__(self, out_dir: Path | str = Path("config/qr_codes")):
        # загрузка .env (один раз — ок)
        load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / "config" / ".env")
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # шаблоны
        self.tmpl_mega = os.getenv("QR_MEGA_TMPL")
        self.tmpl_uni  = os.getenv("QR_UNI_TMPL")
        # дефолты
        self.def_iin   = os.getenv("QR_DEFAULT_IIN", "")
        self.def_client= os.getenv("QR_DEFAULT_CLIENT", "")
        self.def_dist  = os.getenv("QR_DEFAULT_DISTRIBUTOR", "")
        self.def_amount= os.getenv("QR_DEFAULT_AMOUNT", "1")

    @staticmethod
    def _rand6() -> str:
        return str(random.randint(100000, 999999))

    def build_url(self, kind: str, **overrides) -> dict:
        """
        kind: 'megapolis' | 'universal'
        overrides: можно пробросить свои значения (amount, iin, distributor, client, contract/invoiceId)
        return: dict(url=..., id=..., kind=...)
        """
        kind = kind.lower()
        if kind == "megapolis":
            contract = overrides.get("contract", self._rand6())
            url = self.tmpl_mega.format(
                contract=quote(contract),
                iin=quote(overrides.get("iin", self.def_iin)),
                amount=quote(overrides.get("amount", self.def_amount)),
            )
            return {"url": url, "id": contract, "kind": kind}

        if kind == "universal":
            invoice_id = overrides.get("invoiceId", self._rand6())
            url = self.tmpl_uni.format(
                distributor=quote(overrides.get("distributor", self.def_dist)),
                client=quote(overrides.get("client", self.def_client)),
                invoiceId=quote(invoice_id),
                amount=quote(overrides.get("amount", self.def_amount)),
                invoiceTitle=quote(overrides.get("invoiceTitle", invoice_id)),
            )
            return {"url": url, "id": invoice_id, "kind": kind}

        raise ValueError(f"Неизвестный kind: {kind}")

    def png(self, kind: str, **overrides) -> Path:
        """
        Сгенерировать PNG для нужного kind, вернуть путь до файла.
        Имя файла включает kind и id (для удобного выбора из галереи).
        """
        info = self.build_url(kind, **overrides)
        name = f"{info['kind']}_{info['id']}.png"
        path = self.out_dir / name

        qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=10, border=4)
        qr.add_data(info["url"])
        qr.make(fit=True)
        qr.make_image().save(path)
        return path
