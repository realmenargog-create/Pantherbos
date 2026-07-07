# Developed by: Team Alpha

BOT_TOKEN = "8908135285:AAHA80orQac0XgWajfwp_fMefwcS_5rzh9M"
ROOT_ADMIN = "6601602327"

# Channel Logs Configurations
PAYOUT_CHANNEL = "@AlphaPayLogs"
WITHDRAW_CHANNEL = "@KpgWithdraw"

# Internal Memory Clusters (In-Memory Database Layout)
db = {
    "user_list": set(),
    "balances": {},
    "ranks": {},
    "rank_progress": {},
    "upi_ids": {},
    "dynamic_admins": set(),
    "banned_users": set(),
    "tasks": [],
    "user_tasks_completed": {},
    "withdraw_requests": {},
    "withdraw_counter": 1000,
    "total_transactions": 0,
    "total_withdrawals": 0,
    "user_balance_version": {},
    "global_balance_version": 1
}
