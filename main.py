from fastapi import FastAPI, Depends, HTTPException, Request, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from models import User, Wallet, Track, ListeningHistory, Transaction
from schemas import UserCreate, UserOut, WalletOut, TransactionCreate, TransactionOut
from passlib.context import CryptContext
import os
import hashlib
import json
from web3 import Web3, Account
import aiofiles
from typing import List
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="_5#y2L\"F4Q8z\n\xec]/")
app.mount("/static", StaticFiles(directory="templates"), name="static")

templates = Jinja2Templates(directory="templates")
UPLOAD_FOLDER = "uploads"
HASHES_FILE = "uploaded_files_hashes.json"
ALLOWED_EXTENSIONS = {"mp3"}

# Настройка Web3 для BSC Testnet
w3 = Web3(Web3.HTTPProvider("https://bsc-testnet.publicnode.com/"))
TOKEN_ADDRESS = "0xAfB31679785b92a4090e8bA834B43690090c8A19"
SYSTEM_ADDRESS = "0x35cE6A2951ADb4b3e55f08A613148686930aa51E"
SYSTEM_PRIVATE_KEY = "5538c35f959b0083c74bed85be8cc99e2224f4b2dc16630977d0f5fa72bd9260"

ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "allowance", "type": "uint256"},
            {"internalType": "uint256", "name": "needed", "type": "uint256"}
        ],
        "name": "ERC20InsufficientAllowance",
        "type": "error"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "sender", "type": "address"},
            {"internalType": "uint256", "name": "balance", "type": "uint256"},
            {"internalType": "uint256", "name": "needed", "type": "uint256"}
        ],
        "name": "ERC20InsufficientBalance",
        "type": "error"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "approver", "type": "address"}
        ],
        "name": "ERC20InvalidApprover",
        "type": "error"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "receiver", "type": "address"}
        ],
        "name": "ERC20InvalidReceiver",
        "type": "error"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "sender", "type": "address"}
        ],
        "name": "ERC20InvalidSender",
        "type": "error"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"}
        ],
        "name": "ERC20InvalidSpender",
        "type": "error"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "spender", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "Approval",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"}
        ],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]
contract = w3.eth.contract(address=TOKEN_ADDRESS, abi=ABI)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

Base.metadata.create_all(bind=engine)

# Функция для получения оптимальной цены газа
def get_optimal_gas_price():
    gas_price = w3.eth.gas_price
    return max(gas_price, w3.to_wei("1", "gwei"))  # Минимум 1 Gwei

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user

# Главная страница
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Регистрация (POST)
@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "User already exists"})

    hashed_password = pwd_context.hash(password)
    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Генерация нового кошелька
    new_account = w3.eth.account.create()
    address = new_account.address
    private_key = new_account.key.hex()
    seed = hashlib.sha256(new_account.key).hexdigest()

    new_wallet = Wallet(user_id=new_user.id, address=address, seed=seed, private_key=private_key)
    db.add(new_wallet)
    db.commit()

    print(f"New user wallet: {address}")

    system_nonce = w3.eth.get_transaction_count(SYSTEM_ADDRESS)

    # Отправка 0.01 BNB
    bnb_tx = {
        "to": address,
        "value": w3.to_wei("0.01", "ether"),
        "gas": 21000,
        "gasPrice": get_optimal_gas_price(),  # Динамическая цена газа
        "nonce": system_nonce,
        "chainId": 97
    }
    signed_bnb_tx = w3.eth.account.sign_transaction(bnb_tx, SYSTEM_PRIVATE_KEY)
    bnb_tx_hash = w3.eth.send_raw_transaction(signed_bnb_tx.raw_transaction)
    print(f"BNB tx hash: {bnb_tx_hash.hex()}")

    # Начисление 1 токена
    gas_estimate = contract.functions.transfer(address, 1 * 10**18).estimate_gas({'from': SYSTEM_ADDRESS})
    tx = contract.functions.transfer(address, 1 * 10**18).build_transaction({
        "from": SYSTEM_ADDRESS,
        "nonce": system_nonce + 1,
        "gas": gas_estimate + 10000,  # Динамический лимит с запасом
        "gasPrice": get_optimal_gas_price()  # Динамическая цена
    })
    signed_tx = w3.eth.account.sign_transaction(tx, SYSTEM_PRIVATE_KEY)
    token_tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Token transfer tx hash: {token_tx_hash.hex()}")

    w3.eth.wait_for_transaction_receipt(token_tx_hash, timeout=120)

    # Пользователь разрешает системе списывать токены
    MAX_UINT256 = 2**256 - 1
    gas_estimate = contract.functions.approve(SYSTEM_ADDRESS, MAX_UINT256).estimate_gas({'from': address})
    approve_tx = contract.functions.approve(SYSTEM_ADDRESS, MAX_UINT256).build_transaction({
        "from": address,
        "nonce": w3.eth.get_transaction_count(address),
        "gas": gas_estimate + 10000,
        "gasPrice": get_optimal_gas_price()
    })
    signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key)
    approve_tx_hash = w3.eth.send_raw_transaction(signed_approve_tx.raw_transaction)
    print(f"Approve tx hash: {approve_tx_hash.hex()}")

    balance = contract.functions.balanceOf(address).call() / 10**18
    allowance = contract.functions.allowance(address, SYSTEM_ADDRESS).call() / 10**18
    print(f"User balance after registration: {balance} tokens")
    print(f"Allowance for SYSTEM_ADDRESS: {allowance} tokens")

    request.session["logged_in"] = True
    request.session["username"] = username
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

# Регистрация (GET)
@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Логин
@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(None),
    password: str = Form(None),
    private_key: str = Form(None),
    db: Session = Depends(get_db)
):
    if username and password:
        user = db.query(User).filter(User.username == username).first()
        if not user or not pwd_context.verify(password, user.password):
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
        token = username
        wallet = db.query(Wallet).filter(Wallet.user_id == user.id).order_by(Wallet.id.desc()).first()
    elif private_key:
        wallet = db.query(Wallet).filter(Wallet.private_key == private_key).first()
        if not wallet:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid private key"})
        user = db.query(User).filter(User.id == wallet.user_id).first()
        token = user.username
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Provide credentials"})

    request.session["logged_in"] = True
    request.session["username"] = user.username
    request.session["user_wallet_address"] = wallet.address
    
    # Баланс токенов
    token_balance = contract.functions.balanceOf(wallet.address).call() / 10**18
    # Баланс BNB
    bnb_balance = w3.eth.get_balance(wallet.address) / 10**18
    
    return templates.TemplateResponse("wallet_dashboard.html", {
        "request": request,
        "token_balance": token_balance,  # Переименовал для ясности
        "bnb_balance": bnb_balance,      # Новый параметр
        "address": wallet.address,
        "private_key": wallet.private_key
    })

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Логаут
@app.get("/logout", response_class=RedirectResponse)
async def logout(request: Request):
    request.session.pop("logged_in", None)
    request.session.pop("username", None)
    request.session.pop("user_wallet_address", None)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

# Загрузка файла
@app.post("/upload_file", response_class=JSONResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user_wallet_address = request.session.get("user_wallet_address")
    if not user_wallet_address:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if not file.filename.endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_content = await file.read()
    file_hash = hashlib.md5(file_content).hexdigest()
    
    if os.path.exists(HASHES_FILE):
        with open(HASHES_FILE, "r") as f:
            hashes = json.load(f)
        if file_hash in hashes:
            raise HTTPException(status_code=400, detail="File already exists")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)

    hashes = json.load(open(HASHES_FILE, "r")) if os.path.exists(HASHES_FILE) else []
    hashes.append(file_hash)
    with open(HASHES_FILE, "w") as f:
        json.dump(hashes, f)

    # Начисление 0.5 токена
    nonce = w3.eth.get_transaction_count(SYSTEM_ADDRESS)
    gas_estimate = contract.functions.transfer(user_wallet_address, int(0.5 * 10**18)).estimate_gas({'from': SYSTEM_ADDRESS})
    tx = contract.functions.transfer(user_wallet_address, int(0.5 * 10**18)).build_transaction({
        "from": SYSTEM_ADDRESS,
        "nonce": nonce,
        "gas": gas_estimate + 10000,
        "gasPrice": get_optimal_gas_price()
    })
    signed_tx = w3.eth.account.sign_transaction(tx, SYSTEM_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    return {"message": "File uploaded and 0.5 tokens transferred", "tx_hash": tx_hash.hex()}

@app.get("/upload_file", response_class=HTMLResponse)
async def upload_file_get(request: Request):
    if "user_wallet_address" not in request.session:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("upload_file.html", {"request": request})

# Прослушивание трека
@app.get("/listen/{track_id}", response_class=JSONResponse)
async def listen_to_track(
    request: Request,
    track_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_wallet_address = request.session.get("user_wallet_address")
    if not user_wallet_address:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    wallet = db.query(Wallet).filter(Wallet.address == user_wallet_address).first()
    track = db.query(Track).get(track_id)
    recipient_address = SYSTEM_ADDRESS

    balance = contract.functions.balanceOf(wallet.address).call() / 10**18
    if balance < 1:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Списание 1 токена
    gas_estimate = contract.functions.transferFrom(wallet.address, recipient_address, 1 * 10**18).estimate_gas({'from': SYSTEM_ADDRESS})
    tx = contract.functions.transferFrom(wallet.address, recipient_address, 1 * 10**18).build_transaction({
        "from": SYSTEM_ADDRESS,
        "nonce": w3.eth.get_transaction_count(SYSTEM_ADDRESS),
        "gas": gas_estimate + 10000,
        "gasPrice": get_optimal_gas_price()
    })
    signed_tx = w3.eth.account.sign_transaction(tx, SYSTEM_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    listening_history = ListeningHistory(user_id=current_user.id, track_id=track_id)
    db.add(listening_history)
    db.commit()

    return {"message": f"You listened to track {track_id}. 1 token transferred", "tx_hash": tx_hash.hex()}

# Список файлов
@app.get("/list", response_class=JSONResponse)
async def list_files():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.mp3')]
    return files

# Воспроизведение трека
@app.get("/play/{filename}", response_class=FileResponse)
async def play_track(
    request: Request,
    filename: str,
    t: str = None,
    db: Session = Depends(get_db)
):
    user_wallet_address = request.session.get("user_wallet_address")
    if not user_wallet_address:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    recipient_address = SYSTEM_ADDRESS
    balance = contract.functions.balanceOf(user_wallet_address).call() / 10**18
    allowance = contract.functions.allowance(user_wallet_address, SYSTEM_ADDRESS).call() / 10**18

    print(f"User: {user_wallet_address}")
    print(f"Balance before: {balance} tokens")
    print(f"Allowance before: {allowance} tokens")

    if balance < 0.1:
        raise HTTPException(status_code=402, detail="Insufficient token balance (need at least 0.1 token)")
    if allowance < 0.1:
        raise HTTPException(status_code=403, detail=f"Insufficient allowance: {allowance} tokens allowed")

    # Списание 0.1 токена
    nonce = w3.eth.get_transaction_count(SYSTEM_ADDRESS)
    gas_estimate = contract.functions.transferFrom(user_wallet_address, recipient_address, int(0.1 * 10**18)).estimate_gas({'from': SYSTEM_ADDRESS})
    tx = contract.functions.transferFrom(user_wallet_address, recipient_address, int(0.1 * 10**18)).build_transaction({
        "from": SYSTEM_ADDRESS,
        "nonce": nonce,
        "gas": gas_estimate + 10000,
        "gasPrice": get_optimal_gas_price()
    })
    signed_tx = w3.eth.account.sign_transaction(tx, SYSTEM_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"Transaction hash: {tx_hash.hex()} - 0.1 token transferred from {user_wallet_address} to {SYSTEM_ADDRESS}")

    new_balance = contract.functions.balanceOf(user_wallet_address).call() / 10**18
    print(f"Balance after: {new_balance} tokens")

    track_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(track_path):
        raise HTTPException(status_code=404, detail="Track not found")

    response = FileResponse(track_path)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Трансфер токенов
@app.post("/transfer", response_model=TransactionOut)
async def transfer_funds(
    request: Request,
    recipient_address: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    if "username" not in request.session or not request.session.get("logged_in"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    username = request.session["username"]
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sender_wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    balance = contract.functions.balanceOf(sender_wallet.address).call() / 10**18

    if sender_wallet.address == recipient_address:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")
    if balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    sender_bnb_balance = w3.eth.get_balance(sender_wallet.address) / 10**18
    amount_wei = int(amount * 10**18)  # Преобразуем в wei
    gas_estimate = contract.functions.transfer(recipient_address, amount_wei).estimate_gas({'from': sender_wallet.address})
    gas_cost = gas_estimate * get_optimal_gas_price() / 10**18
    if sender_bnb_balance < gas_cost:
        raise HTTPException(status_code=400, detail=f"Insufficient BNB for gas: need ~{gas_cost:.6f} BNB, have {sender_bnb_balance:.6f} BNB")

    tx = contract.functions.transfer(recipient_address, amount_wei).build_transaction({
        "from": sender_wallet.address,
        "nonce": w3.eth.get_transaction_count(sender_wallet.address),
        "gas": gas_estimate + 10000,
        "gasPrice": get_optimal_gas_price(),
        "chainId": 97
    })
    signed_tx = w3.eth.account.sign_transaction(tx, sender_wallet.private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(f"Transfer tx hash: {tx_hash.hex()} - {amount} tokens from {sender_wallet.address} to {recipient_address}")

    # Сохранение amount как целого числа в wei
    new_transaction = Transaction(
        sender=sender_wallet.address,
        recipient=recipient_address,
        amount=amount_wei  # Сохраняем в wei
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    # Преобразуем обратно в читаемый формат для ответа
    new_transaction.amount = amount  # Возвращаем как float для удобства
    return new_transaction

# История транзакций
@app.get("/transaction_history/{wallet_address}", response_class=HTMLResponse)
async def transaction_history(
    request: Request,
    wallet_address: str,
    db: Session = Depends(get_db)
):
    if "username" not in request.session:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    transactions = db.query(Transaction).filter(
        (Transaction.sender == wallet_address) | (Transaction.recipient == wallet_address)
    ).all()
    return templates.TemplateResponse("transaction_history.html", {"request": request, "transactions": transactions})

# Баланс
@app.get("/get_balance", response_class=JSONResponse)
async def get_balance(wallet_address: str):
    if not wallet_address:
        raise HTTPException(status_code=400, detail="Wallet address is required")
    
    token_balance = contract.functions.balanceOf(wallet_address).call() / 10**18
    bnb_balance = w3.eth.get_balance(wallet_address) / 10**18
    
    return {
        "token_balance": token_balance,
        "bnb_balance": bnb_balance
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
