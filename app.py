import http.server, socketserver, json, random, time, hashlib, secrets, os, webbrowser
from urllib.parse import parse_qs

# ================= PORT =================
PORT = int(os.environ.get("PORT", 10000))

# ================= DATABASE =================
DB = "users.json"
try:
    with open(DB, "r") as f:
        users = json.load(f)
except:
    users = {}

def save():
    with open(DB, "w") as f:
        json.dump(users, f, indent=2)

# ================= SECURITY =================
def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ================= SESSION =================
sessions = {}

def create_session(user):
    token = secrets.token_hex(16)
    sessions[token] = user
    return token

def get_user(headers):
    cookie = headers.get("Cookie")
    if not cookie:
        return None
    for c in cookie.split(";"):
        if "session=" in c:
            return sessions.get(c.strip().split("=")[1])
    return None

# ================= OTP =================
otp_store = {}

def generate_otp(username, password):
    otp = str(random.randint(100000, 999999))
    otp_store[username] = {
        "otp": otp,
        "pw": password,
        "time": time.time()
    }
    print(f"🔥 OTP for {username}: {otp}")

# ================= PRODUCTS =================
products = {
    "Almonds": {"price": 500, "img": "https://upload.wikimedia.org/wikipedia/commons/3/36/Almonds.jpg"},
    "Cashews": {"price": 800, "img": "https://upload.wikimedia.org/wikipedia/commons/2/2f/Cashew_nuts.jpg"},
    "Walnuts": {"price": 900, "img": "https://upload.wikimedia.org/wikipedia/commons/1/1b/Walnuts.jpg"}
}

# ================= UI =================
def page(body):
    return f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <title>The Nut Project</title>
    <style>
    body {{
        margin:0;
        font-family:Arial;
        background:#eaeded;
    }}

    .nav {{
        background:#131921;
        color:white;
        padding:15px 30px;
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}

    .logo {{
        font-size:24px;
        color:#ff9900;
        font-weight:bold;
    }}

    .container {{
        padding:20px;
    }}

    .cart-box {{
        background:white;
        padding:15px;
        border-radius:10px;
        margin-bottom:20px;
        box-shadow:0 2px 6px rgba(0,0,0,0.2);
    }}

    .grid {{
        display:grid;
        grid-template-columns:repeat(auto-fill,minmax(220px,1fr));
        gap:20px;
    }}

    .card {{
        background:white;
        padding:15px;
        border-radius:10px;
        text-align:center;
        box-shadow:0 2px 8px rgba(0,0,0,0.2);
        transition:0.3s;
    }}

    .card:hover {{
        transform:scale(1.05);
    }}

    .card img {{
        width:120px;
        height:120px;
        object-fit:cover;
    }}

    button {{
        padding:10px;
        border:none;
        border-radius:5px;
        cursor:pointer;
        font-weight:bold;
    }}

    .buy {{
        background:#ffd814;
        width:100%;
    }}

    .buy:hover {{
        background:#f7ca00;
    }}

    .pay {{
        background:#ffa41c;
        width:100%;
        margin-top:10px;
    }}

    .pay:hover {{
        background:#ff8f00;
    }}

    input {{
        padding:10px;
        margin:5px;
        border-radius:5px;
        border:1px solid #ccc;
    }}
    </style>
    </head>

    <body>

    <div class="nav">
        <div class="logo">🌰 Nut Project</div>
        <div>Online Store</div>
    </div>

    <div class="container">
    {body}
    </div>

    </body>
    </html>
    """

# ================= PAGES =================
def login_page():
    return page("""
    <h2>Login / Register</h2>
    <form method="POST">
    <input name="username" placeholder="Username"><br>
    <input name="password" type="password" placeholder="Password"><br>
    <button name="action" value="register">Register</button>
    <button name="action" value="login">Login</button>
    </form>
    """)

def otp_page():
    return page("""
    <h2>Enter OTP (check terminal)</h2>
    <form method="POST">
    <input name="otp"><br>
    <button name="verify">Verify</button>
    </form>
    """)

def home(user):
    cart = users[user]["cart"]
    total = sum(products[i]["price"] for i in cart)

    items = ""
    for name, d in products.items():
        items += f"""
        <div class="card">
            <img src="{d['img']}">
            <h3>{name}</h3>
            <p>₹{d['price']}</p>
            <form method="POST">
            <button class="buy" name="buy" value="{name}">Add to Cart</button>
            </form>
        </div>
        """

    return page(f"""
    <h2>Welcome {user}</h2>

    <div class="cart-box">
    <h3>Cart: {cart}</h3>
    <h3>Total: ₹{total}</h3>

    <form method="POST">
    <button class="pay" name="pay">Checkout</button>
    </form>
    </div>

    <div class="grid">
    {items}
    </div>
    """)

# ================= SERVER =================
class Handler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        user = get_user(self.headers)
        if user and user in users:
            self.respond(home(user))
        else:
            self.respond(login_page())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        params = parse_qs(self.rfile.read(length).decode())
        user = get_user(self.headers)

        if "action" in params:
            u = params["username"][0]
            p = params["password"][0]

            if params["action"][0] == "login":
                if u in users and users[u]["pw"] == hash_pw(p):
                    self.login(u)
                else:
                    self.respond("<h2>Wrong login</h2>")
            else:
                generate_otp(u, p)
                self.respond(otp_page())

        elif "verify" in params:
            otp = params["otp"][0]
            for u, d in list(otp_store.items()):
                if otp == d["otp"]:
                    users[u] = {"pw": hash_pw(d["pw"]), "cart": []}
                    save()
                    del otp_store[u]
                    self.login(u)
                    return
            self.respond("<h2>Invalid OTP</h2>")

        elif "buy" in params and user:
            users[user]["cart"].append(params["buy"][0])
            save()
            self.redirect()

        elif "pay" in params and user:
            users[user]["cart"] = []
            save()
            self.respond(page("<h2>Order Placed 🎉</h2>"))

    def login(self, user):
        token = create_session(user)
        self.send_response(302)
        self.send_header("Set-Cookie", f"session={token}; Path=/")
        self.send_header("Location", "/")
        self.end_headers()

    def redirect(self):
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def respond(self, html):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(html.encode())

# ================= SERVER START =================
class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

HOST = "0.0.0.0"

# Auto open browser (only local)
if "RENDER" not in os.environ:
    webbrowser.open(f"http://localhost:{PORT}")

with Server((HOST, PORT), Handler) as server:
    print(f"🚀 Running at http://localhost:{PORT}")
    server.serve_forever()