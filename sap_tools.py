import os
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

SAP_URL = os.getenv("SAP_BASE_URL")
AUTH = (os.getenv("SAP_USER"), os.getenv("SAP_PASSWORD"))

@tool
def get_material_stock(material_id: str) -> dict:
    """
    Verilen Malzeme Numarası (Material ID) için SAP sisteminden
    stok miktarı, birimi ve kritik stok durumunu döner.
    """

    endpoint = (
        f"{SAP_URL}/StockInfo"
        f"?$filter=MaterialID eq '{material_id}'"
        f"&$format=json"
    )

    print(f"\n[TOOL LOG] SAP sorgusu başlatıldı. MaterialID: {material_id}")

    try:
        response = requests.get(
            endpoint,
            auth=AUTH,
            verify=False,   # ⚠️ sadece test ortamı
            timeout=10
        )

        if response.status_code != 200:
            return {
                "Hata": True,
                "Mesaj": f"SAP HTTP {response.status_code}",
                "Detay": response.text
            }

        data = response.json()
        results = data.get("d", {}).get("results", [])

        if not results:
            return {
                "Hata": False,
                "Bulundu_Mu": False,
                "Mesaj": f"{material_id} numaralı malzeme bulunamadı."
            }

        item = results[0]

        return {
            "Hata": False,
            "Bulundu_Mu": True,
            "Malzeme_Kodu": item.get("MaterialID"),
            "Aciklama": item.get("MaterialDesc"),
            "Stok_Miktari": item.get("StockQuantity"),
            "Birim": item.get("Unit"),
            "Kritik_Seviye_Mi": item.get("IsCritical")
        }

    except requests.exceptions.Timeout:
        return {
            "Hata": True,
            "Mesaj": "SAP zaman aşımı (timeout)"
        }

    except Exception as e:
        return {
            "Hata": True,
            "Mesaj": "Beklenmeyen hata",
            "Detay": str(e)
        }
