# Developed by: Team Alpha
import os
import json
import re
import threading
from flask import Flask, request
import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.BOT_TOKEN, threaded=False)
app = Flask(__name__)

# ==========================================
# 🎨 UI FORMATTING ENGINES (Combo-3 Hybrid)
# ==========================================
def render_header(title):
    return f"┌──────────────────────┐\n 💎 <b>{title.upper()}</b> \n└──────────────────────┘\n"

def get_user_rank(user_id):
    uid = str(user_id)
    if uid not in config.db["ranks"]:
        config.db["ranks"][uid] = "Bronze"
        config.db["rank_progress"][uid] = 0
    return config.db["ranks"][uid], config.db["rank_progress"][uid]

def get_balance(user_id):
    uid = str(user_id)
    g_ver = config.db["global_balance_version"]
    u_ver = config.db["user_balance_version"].get(uid, 1)
    
    if g_ver != u_ver:
        config.db["balances"][uid] = 0.00
        config.db["user_balance_version"][uid] = g_ver
        
    if uid not in config.db["balances"]:
        config.db["balances"][uid] = 0.00
        config.db["user_balance_version"][uid] = g_ver
        
    return float(config.db["balances"][uid])

def add_balance(user_id, amount):
    uid = str(user_id)
    current = get_balance(user_id)
    config.db["balances"][uid] = round(current + float(amount), 2)
    return config.db["balances"][uid]

def is_admin(user_id):
    uid = str(user_id)
    return uid == config.ROOT_ADMIN or uid in config.db["dynamic_admins"]

# ==========================================
# 🛡️ GLOBAL AUTHENTICATION & SPAM GATES
# ==========================================
@bot.message_handler(func=lambda msg: str(msg.from_user.id) in config.db["banned_users"])
def handle_banned(message):
    bot.send_message(message.chat.id, "🚨 <b>ACCESS DENIED:</b> Your account is permanently banned.", parse_mode="HTML")

# ==========================================
# 💎 CORE BOT COMMANDS
# ==========================================
@bot.message_handler(commands=['start'])
def command_start(message):
    uid = str(message.from_user.id)
    config.db["user_list"].add(uid)
    
    rank_name, xp = get_user_rank(uid)
    bal = get_balance(uid)
    
    txt = render_header("AlphaPay Wallet")
    txt += f"• Account ID ──> <code>{uid}</code>\n"
    txt += f"• Net Balance ──> ₹<code>{bal:.2f}</code>\n"
    txt += f"• Tier Rank ──> <code>{rank_name}</code> (XP: <code>{xp}%</code>)\n"
    txt += "──────────────────────\n"
    txt += "Select an operation from the secure matrix panel below:"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💰 Wallet", callback_data="/menu_wallet"),
        types.InlineKeyboardButton("💸 Send Money", callback_data="/menu_send"),
        types.InlineKeyboardButton("🏧 Withdraw", callback_data="/menu_withdraw"),
        types.InlineKeyboardButton("📋 Task Earn", callback_data="/menu_tasks"),
        types.InlineKeyboardButton("💳 Link UPI", callback_data="/menu_linkupi")
    )
    
    if is_admin(uid):
        markup.add(types.InlineKeyboardButton("🛠️ Admin Panel", callback_data="/admin_main"))
        
    bot.send_message(message.chat.id, txt, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "/menu_wallet")
def callback_wallet(call):
    uid = str(call.from_user.id)
    bal = get_balance(uid)
    rank, xp = get_user_rank(uid)
    
    txt = render_header("Wallet Metrics")
    txt += f"• Core ID ──> <code>{uid}</code>\n"
    txt += f"• Assets ──> ₹<code>{bal:.2f}</code>\n"
    txt += f"• Rank Pointer ──> <code>{rank}</code> [<code>{xp}/100 XP</code>]\n"
    txt += "──────────────────────\n"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Return Dashboard", callback_data="/menu_home"))
    bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "/menu_home")
def callback_home(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    command_start(call)

# ==========================================
# 💳 LINK UPI IMPLEMENTATION
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "/menu_linkupi")
def callback_linkupi(call):
    txt = render_header("UPI Account Linker")
    txt += "Please provide your dynamic payment handle reference.\n\n" \
           "👉 <b>Format Matrix:</b> <code>username@bank</code>\n" \
           "──────────────────────\n" \
           "✏️ <i>Type your correct UPI ID handle directly in chat:</i>"
    
    msg = bot.send_message(call.message.chat.id, txt, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_upi_saving)

def process_upi_saving(message):
    can_proceed = True
    user_input = message.text.strip()
    uid = str(message.from_user.id)
    
    if "@" not in user_input or len(user_input) < 5:
        can_proceed = False
        bot.send_message(message.chat.id, "❌ <b>INVALID STRUCTURE:</b> UPI format matching failed. Process aborted.", parse_mode="HTML")
        
    if can_proceed:
        config.db["upi_ids"][uid] = user_input
        txt = render_header("Link Successful")
        txt += f"• Account Target ──> <code>{uid}</code>\n" \
               f"• Destination UPI ──> <code>{user_input}</code>\n" \
               f"• Ledger Sync ──> 🟢 <code>[BOUNDED]</code>"
        bot.send_message(message.chat.id, txt, parse_mode="HTML")

# ==========================================
# 💸 SECURE P2P PAYMENT SYSTEM
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "/menu_send")
def callback_send_prompt(call):
    txt = render_header("Peer Transfer Module")
    txt += "Execute instant capital transfer using account IDs.\n\n" \
           "👉 <b>Command String Format:</b>\n" \
           " └── <code>Target_ID Amount</code> (e.g. <code>6601602327 50</code>)\n" \
           "──────────────────────\n" \
           "✏️ <i>Enter details below:</i>"
    msg = bot.send_message(call.message.chat.id, txt, parse_mode="HTML")
    bot.register_next_step_handler(msg, execute_p2p_transfer)

def execute_p2p_transfer(message):
    can_proceed = True
    sender_id = str(message.from_user.id)
    input_text = message.text.strip().split()
    
    if len(input_text) < 2:
        can_proceed = False
        bot.send_message(message.chat.id, "❌ <b>PARSING FAILED:</b> Missing fields. Use: <code>ID Amount</code>", parse_mode="HTML")
        
    if can_proceed:
        target_id = input_text[0]
        try:
            amount = round(float(input_text[1]), 2)
        except (ValueError, IndexError):
            amount = 0.00
            can_proceed = False
            bot.send_message(message.chat.id, "❌ <b>MATHEMATICAL EXCEPTION:</b> Amount must be a positive float value.", parse_mode="HTML")
            
    if can_proceed:
        if amount <= 0:
            can_proceed = False
            bot.send_message(message.chat.id, "❌ <b>RANGE FAULT:</b> Transacted value must exceed zero bounds.", parse_mode="HTML")
        elif target_id == sender_id:
            can_proceed = False
            bot.send_message(message.chat.id, "❌ <b>SECURITY REJECTION:</b> Self-transacting loops are forbidden.", parse_mode="HTML")
        elif target_id not in config.db["user_list"]:
            can_proceed = False
            bot.send_message(message.chat.id, "❌ <b>NODE REFUSAL:</b> Target recipient profile not initialized in database.", parse_mode="HTML")
        elif get_balance(sender_id) < amount:
            can_proceed = False
            bot.send_message(message.chat.id, "❌ <b>LIQUIDITY ERROR:</b> Insufficient funds in active wallet matrix.", parse_mode="HTML")

    if can_proceed:
        add_balance(sender_id, -amount)
        add_balance(target_id, amount)
        config.db["total_transactions"] += 1
        
        cashback = round(amount * 0.01, 2)
        admin_bonus = 0.50 if is_admin(sender_id) else 0.00
        
        if admin_bonus > 0:
            add_balance(target_id, admin_bonus)
        else:
            add_balance(sender_id, cashback)
            
        rank, xp = get_user_rank(sender_id)
        new_xp = xp + 5
        if new_xp >= 100:
            tiers = ["Bronze", "Silver", "Gold", "Diamond"]
            current_idx = tiers.index(rank) if rank in tiers else 0
            next_idx = min(current_idx + 1, len(tiers) - 1)
            config.db["ranks"][sender_id] = tiers[next_idx]
            config.db["rank_progress"][sender_id] = 0
            bot.send_message(message.chat.id, f"🎉 <b>EVOLUTION UPGRADE:</b> Your profile evolved to <code>{tiers[next_idx]}</code> Tier!", parse_mode="HTML")
        else:
            config.db["rank_progress"][sender_id] = new_xp
            
        masked_target = target_id[:3] + "xxxx" + target_id[-3:] if len(target_id) > 6 else "xxxxxx"
        
        sender_txt = render_header("Settle Receipt")
        sender_txt += f"• Paid To ──> <code>{masked_target}</code>\n" \
                      f"• Dispatched ──> ₹<code>{amount:.2f}</code>\n" \
                      f"• Cashback ──> ₹<code>{cashback:.2f}</code>\n" \
                      f"• Condition ──> 🟢 <code>[SETTLED_LIVE]</code>"
        
        task_markup = types.InlineKeyboardMarkup()
        task_markup.add(types.InlineKeyboardButton("📋 TASK EARN", callback_data="/menu_tasks"))
        bot.send_message(message.chat.id, sender_txt, parse_mode="HTML", reply_markup=task_markup)
        
        recv_txt = render_header("Funds Received")
        recv_txt += f"• From Node ──> <code>{sender_id[:3]}xxxx{sender_id[-3:]}</code>\n" \
                    f"• Credited ──> ₹<code>{amount:.2f}</code>\n"
        if admin_bonus > 0:
            recv_txt += f"• Admin Bonus ──> ₹<code>{admin_bonus:.2f}</code>\n"
      recv_txt += f"• Condition ──> 🟢 [CREDITED]"bot.send_message(int(target_id), recv_txt, parse_mode="HTML")chan_txt = f"🔔 Transaction Ledger Alert\n" f"──────────────────────\n" f"• Sender ──> {sender_id}\n" f"• Recipient ──> {target_id}\n" f"• Amount ──> ₹{amount:.2f}\n" f"• Sender Rank ──> {config.db['ranks'].get(sender_id, 'Bronze')}\n" f"──────────────────────"try:bot.send_message(config.PAYOUT_CHANNEL, chan_txt, parse_mode="HTML")except Exception:pass==========================================🏧 WITHDRAWAL SYSTEM==========================================@bot.callback_query_handler(func=lambda call: call.data == "/menu_withdraw")def callback_withdraw_prompt(call):uid = str(call.from_user.id)if uid not in config.db["upi_ids"]:bot.answer_callback_query(call.id, "⚠️ LINK UPI FIRST: Connect an active address handle via the panel menu.", show_alert=True)returnbal = get_balance(uid)txt = render_header("Asset Withdrawal Portal")txt += f"• Active Balance ──> ₹{bal:.2f}\n" f"• Target Endpoint ──> {config.db['upi_ids'][uid]}\n" f"• Min Limit ──> ₹50.00\n" "──────────────────────\n" "✏️ Type amount to process extraction:"msg = bot.send_message(call.message.chat.id, txt, parse_mode="HTML")bot.register_next_step_handler(msg, process_withdrawal_request)def process_withdrawal_request(message):can_proceed = Trueuid = str(message.from_user.id)try:amount = round(float(message.text.strip()), 2)except (ValueError, TypeError):amount = 0.00can_proceed = Falsebot.send_message(message.chat.id, "❌ INPUT ERROR: Numeric float structures required.", parse_mode="HTML")if can_proceed:if amount < 50.00:can_proceed = Falsebot.send_message(message.chat.id, "❌ LIMIT CONTRACTION: Minimum withdrawal limit is ₹50.00", parse_mode="HTML")elif get_balance(uid) < amount:can_proceed = Falsebot.send_message(message.chat.id, "❌ LIQUIDITY FAULT: Requested value exceeds account balance index.", parse_mode="HTML")if can_proceed:add_balance(uid, -amount)config.db["withdraw_counter"] += 1req_id = f"REQ{config.db['withdraw_counter']}"config.db["withdraw_requests"][req_id] = {"uid": uid,"amount": amount,"upi": config.db["upi_ids"][uid]}bot.send_message(message.chat.id, f"✅ REQUEST QUEUED: Asset volume isolated. Request Tracking ID: {req_id}", parse_mode="HTML")adm_txt = f"⚠️ WITHDRAWAL REQUEST PENDING\n" f"──────────────────────\n" f"• Request ID ──> {req_id}\n" f"• Source ID ──> {uid}\n" f"• Cash Value ──> ₹{amount:.2f}\n" f"• Destination UPI ──> {config.db['upi_ids'][uid]}\n" f"──────────────────────"markup = types.InlineKeyboardMarkup()markup.add(types.InlineKeyboardButton("🟢 Approve", callback_data=f"/wd_ap_{req_id}"),types.InlineKeyboardButton("🔴 Reject", callback_data=f"/wd_rj_{req_id}"))try:bot.send_message(config.WITHDRAW_CHANNEL, adm_txt, parse_mode="HTML", reply_markup=markup)except Exception:pass@bot.callback_query_handler(func=lambda call: call.data.startswith("/wd_"))def callback_admin_withdrawal_decide(call):if not is_admin(call.from_user.id):bot.answer_callback_query(call.id, "🚨 Unauthorized action node.", show_alert=True)returndata = call.data.split("_")action = data[1]req_id = data[2]if req_id not in config.db["withdraw_requests"]:bot.answer_callback_query(call.id, "❌ Request element expired or cleared from heap memory blocks.", show_alert=True)returnreq_meta = config.db["withdraw_requests"][req_id]user_target = req_meta["uid"]cash_value = req_meta["amount"]if action == "ap":config.db["total_withdrawals"] += 1bot.edit_message_text(call.message.text + "\n\n📌 STATUS LEDGER ──> 🟢 APPROVED/SETTLED", call.message.chat.id, call.message.message_id, parse_mode="HTML")bot.send_message(int(user_target), f"┌──────────────────────┐\n ✅ WITHDRAWAL SETTLED \n└──────────────────────┘\n• Tracking ──> {req_id}\n• Credit ──> ₹{cash_value:.2f} transferred to linked bank account lines.", parse_mode="HTML")else:add_balance(user_target, cash_value)bot.edit_message_text(call.message.text + "\n\n📌 STATUS LEDGER ──> 🔴 REJECTED/REVERSED", call.message.chat.id, call.message.message_id, parse_mode="HTML")bot.send_message(int(user_target), f"❌ WITHDRAWAL REFUSED: Request ID {req_id} was declined. Funds reverted onto wallet balance assets pool.", parse_mode="HTML")del config.db["withdraw_requests"][req_id]==========================================📋 RECURSIVE TASK MANAGEMENT ENGINE==========================================@bot.callback_query_handler(func=lambda call: call.data == "/menu_tasks")def callback_render_user_tasks(call):uid = str(call.from_user.id)tasks_pool = config.db["tasks"]completed = config.db["user_tasks_completed"].get(uid, set())active_task = Nonetask_idx = -1for idx, t in enumerate(tasks_pool):if t["id"] not in completed and t["claimed_count"] < t["limit"]:active_task = ttask_idx = idxbreakif not active_task:bot.edit_message_text("┌──────────────────────┐\n 🎉 TASKS LOG MATRIX EMPTY \n└──────────────────────┘\n• status ──> COMPLETED_ALL\n\nNo premium monetization campaigns available right now.", call.message.chat.id, call.message.message_id, parse_mode="HTML")returntxt = render_header(f"Campaign Node #{active_task['id']}")txt += f"• Reward Pool ──> ₹{active_task['reward']:.2f}\n" f"• Capacity Caps ──> {active_task['claimed_count']}/{active_task['limit']} Engaged\n" f"──────────────────────\n" f"👉 Join mandatory resource below and tap confirmation block:"markup = types.InlineKeyboardMarkup()markup.add(types.InlineKeyboardButton("📺 Join Channel Link", url=active_task["link"]))markup.add(types.InlineKeyboardButton("✅ Confirm Done", callback_data=f"/verify_t_{active_task['id']}_{task_idx}"))bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)@bot.callback_query_handler(func=lambda call: call.data.startswith("/verify_t_"))def callback_audit_task_clearance(call):uid = str(call.from_user.id)data = call.data.split("_")task_id = int(data[2])task_idx = int(data[3])if task_idx >= len(config.db["tasks"]):bot.answer_callback_query(call.id, "❌ Campaign index structure out of operational bounds.", show_alert=True)returntask = config.db["tasks"][task_idx]chan_username = task["link"].replace("t.me", "").replace("@", "").strip()try:member = bot.get_chat_member(f"@{chan_username}", call.from_user.id)is_joined = member.status in ["member", "administrator", "creator"]except Exception:is_joined = Trueif not is_joined:bot.answer_callback_query(call.id, "⚠️ JOIN FIRST: You have not joined the channel network element yet!", show_alert=True)else:if uid not in config.db["user_tasks_completed"]:config.db["user_tasks_completed"][uid] = set()config.db["user_tasks_completed"][uid].add(task_id)task["claimed_count"] += 1add_balance(uid, task["reward"])bot.answer_callback_query(call.id, f"🎉 Campaign cleared! Credit Added: +₹{task['reward']:.2f}", show_alert=False)callback_render_user_tasks(call)==========================================🛠️ CENTRAL ADMINISTRATIVE PANEL==========================================@bot.callback_query_handler(func=lambda call: call.data == "/admin_main")def callback_admin_hub(call):if not is_admin(call.from_user.id): returntxt = render_header("Alpha Terminal Panel")txt += "Authorized administrative management console execution blocks dashboard:\n"markup = types.InlineKeyboardMarkup(row_width=2)markup.add(types.InlineKeyboardButton("➕ Add Balance", callback_data="/adm_addbal"),types.InlineKeyboardButton("➖ Remove Balance", callback_data="/adm_rembal"),types.InlineKeyboardButton("📢 Broadcast Blast", callback_data="/adm_bcast"),types.InlineKeyboardButton("📝 Construct Task", callback_data="/adm_createtask"),types.InlineKeyboardButton("📊 System Metrics", callback_data="/adm_statscenter"),types.InlineKeyboardButton("🚨 Account Ban Lock", callback_data="/adm_banprompt"))bot.send_message(call.message.chat.id, txt, parse_mode="HTML", reply_markup=markup)@bot.callback_query_handler(func=lambda call: call.data == "/adm_statscenter")def callback_admin_stats(call):if not is_admin(call.from_user.id): returntot_users = len(config.db["user_list"])tot_bal = sum(config.db["balances"].values())txt = render_header("System Topology Metrics")txt += f" • Aggregate Members ──> {tot_users} Nodes\n" f" • Liquidity Pools ──> ₹{tot_bal:.2f} Liability\n" f" • Ledger Actions ──> {config.db['total_transactions']} Transactions\n" f" • Settlements ──> {config.db['total_withdrawals']} Payouts\n" f"──────────────────────"bot.send_message(call.message.chat.id, txt, parse_mode="HTML")@bot.callback_query_handler(func=lambda call: call.data == "/adm_addbal")def callback_adm_addbal_prompt(call):if not is_admin(call.from_user.id): returnmsg = bot.send_message(call.message.chat.id, "✏️ Enter Target: User_ID Amount", parse_mode="HTML")bot.register_next_step_handler(msg, process_admin_addbal)def process_admin_addbal(message):if not is_admin(message.from_user.id): returnparts = message.text.strip().split()if len(parts) >= 2:t_id, amt = parts[0], float(parts[1])new_b = add_balance(t_id, amt)bot.send_message(message.chat.id, f"✅ Target ID {t_id} balance credited. Current: ₹{new_b:.2f}", parse_mode="HTML")@bot.callback_query_handler(func=lambda call: call.data == "/adm_createtask")def callback_adm_task_prompt(call):if not is_admin(call.from_user.id): returnmsg = bot.send_message(call.message.chat.id, "✏️ Format: Link Reward Limit\n(e.g., t.me 5.50 500)", parse_mode="HTML")bot.register_next_step_handler(msg, process_admin_task_creation)def process_admin_task_creation(message):if not is_admin(message.from_user.id): returnparts = message.text.strip().split()if len(parts) >= 3:link = parts[0]reward = float(parts[1])limit = int(parts[2])t_id = len(config.db["tasks"]) + 101config.db["tasks"].append({"id": t_id,"link": link,"reward": reward,"limit": limit,"claimed_count": 0})bot.send_message(message.chat.id, f"✅ MONETIZATION TASK DEPLOYED: Task ID {t_id} created successfully.", parse_mode="HTML")==========================================📢 BROADCAST SYSTEM==========================================@bot.callback_query_handler(func=lambda call: call.data == "/adm_bcast")def callback_adm_bcast_prompt(call):if not is_admin(call.from_user.id): returnmsg = bot.send_message(call.message.chat.id, "✏️ Enter text message string layout content to blast globally across system network:", parse_mode="HTML")bot.register_next_step_handler(msg, process_admin_broadcast)def process_admin_broadcast(message):if not is_admin(message.from_user.id): returntext_payload = message.text.strip()bcast_txt = render_header("Global Broadcast System") + f"{text_payload}\n" f"──────────────────────\n" f"📊 Notice broadcasted uniformly via core admin arrays nodes blocks."def run_broadcast_async():for user_node in list(config.db["user_list"]):try:bot.send_message(int(user_node), bcast_txt, parse_mode="HTML")except Exception:passthreading.Thread(target=run_broadcast_async).start()bot.send_message(message.chat.id, "🟢 BROADCAST ENGINE DEPLOYED: Async data transmission thread triggered successfully.", parse_mode="HTML")==========================================📡 PRODUCTION WEBHOOK WEB PORTAL ENTRY==========================================@app.route('/' + config.BOT_TOKEN, methods=['POST'])def getMessage():json_string = request.get_data().decode('utf-8')update = telebot.types.Update.de_json(json_string)bot.process_new_updates([update])return "!", 200@app.route("/")def webhook():bot.remove_webhook()host_url = request.url_root.replace("http://", "https://")bot.set_webhook(url=host_url + config.BOT_TOKEN)return "AlphaPay Core Terminal System Online Matrix Infrastructure Verified.", 200if name == "main":app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000))
