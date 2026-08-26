import requests

API_URL = "http://127.0.0.1:8000/sae/"

nanda_data = [
    {
        "code": "00146",
        "description_en": "Anxiety",
        "description_pt": "Ansiedade",
        "intervention_en": "Establish therapeutic communication and monitor vital signs.",
        "intervention_pt": "Estabelecer comunicação terapêutica e monitorar sinais vitais."
    },
    {
        "code": "00029",
        "description_en": "Decreased Cardiac Output",
        "description_pt": "Débito Cardíaco Diminuído",
        "intervention_en": "Monitor continuous ECG and evaluate hemodynamic status.",
        "intervention_pt": "Monitorar ECG contínuo e avaliar o estado hemodinâmico."
    }
]

for entry in nanda_data:
    response = requests.post(API_URL, json=entry)
    if response.status_code == 200:
        print(f"Successfully added NANDA: {entry['code']} (EN/PT)")
    else:
        print(f"Failed to add {entry['code']}: {response.text}")
