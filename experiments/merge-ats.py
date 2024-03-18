import merge
from merge.client import Merge

client = Merge(api_key="YOUR_API_KEY", account_token="YOUR_ACCOUNT_TOKEN")



import merge
from merge.client import Merge

merge_client = Merge(
    api_key="<YOUR_API_KEY>", 
    account_token="<YOUR_ACCOUNT_TOKEN>")

candidate = merge_client.ats.candidates.retrieve(
    id="521b18c2-4d01-4297-b451-19858d07c133")
