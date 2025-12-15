from typing import List, Dict, Any

ACCOUNTS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Account 1",
        "strategy": "SH Swing",
        "holding_period": "1-5D",
        "color": "bg-red-600",
        "hover_color": "hover:bg-red-500",
        "text_color": "text-red-500",
        "border_color": "border-red-600"
    },
    {
        "id": 2,
        "name": "Account 2",
        "strategy": "Swing/Sq",
        "holding_period": "2-20D",
        "color": "bg-green-600",
        "hover_color": "hover:bg-green-500",
        "text_color": "text-green-500",
        "border_color": "border-green-600"
    },
    {
        "id": 3,
        "name": "Account 3",
        "strategy": "POS- BO/SQ",
        "holding_period": "2-20W (6m)",
        "color": "bg-yellow-600",
        "hover_color": "hover:bg-yellow-500",
        "text_color": "text-yellow-500",
        "border_color": "border-yellow-600"
    },
    {
        "id": 4,
        "name": "Account 4",
        "strategy": "POS-HVOL",
        "holding_period": "2-20W (6m)",
        "color": "bg-yellow-600",
        "hover_color": "hover:bg-yellow-500",
        "text_color": "text-yellow-500",
        "border_color": "border-yellow-600"
    },
    {
        "id": 5,
        "name": "Account 5",
        "strategy": "POS-PAT",
        "holding_period": "2-20W (6m)",
        "color": "bg-yellow-600",
        "hover_color": "hover:bg-yellow-500",
        "text_color": "text-yellow-500",
        "border_color": "border-yellow-600"
    },
    {
        "id": 6,
        "name": "Account 6",
        "strategy": "INV",
        "holding_period": "3M-2Y",
        "color": "bg-blue-600",
        "hover_color": "hover:bg-blue-500",
        "text_color": "text-blue-500",
        "border_color": "border-blue-600"
    },
    {
        "id": 7,
        "name": "Account 7",
        "strategy": "OPT-Swing",
        "holding_period": "1D-90D",
        "color": "bg-red-600",
        "hover_color": "hover:bg-red-500",
        "text_color": "text-red-500",
        "border_color": "border-red-600"
    },
    {
        "id": 8,
        "name": "Account 8",
        "strategy": "Lot",
        "holding_period": "1-5D",
        "color": "bg-red-600",
        "hover_color": "hover:bg-red-500",
        "text_color": "text-red-500",
        "border_color": "border-red-600"
    },
    {
        "id": 9,
        "name": "Ref/SOY/401K",
        "strategy": "Reference",
        "holding_period": "N/A",
        "color": "bg-gray-600",
        "hover_color": "hover:bg-gray-500",
        "text_color": "text-gray-400",
        "border_color": "border-gray-600"
    },
]

def get_account_by_id(account_id: int):
    for account in ACCOUNTS:
        if account["id"] == account_id:
            return account
    return ACCOUNTS[0] # Default
