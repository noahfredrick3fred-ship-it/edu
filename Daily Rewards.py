from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, timedelta

app = Flask(_name_)

# --- Database Setup ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///daily_rewards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(50), default='Realist')
    coins = db.Column(db.Integer, default=0)
    gems = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    last_claim_date = db.Column(db.Date, nullable=True)

class Reward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_number = db.Column(db.Integer, nullable=False)
    coins = db.Column(db.Integer, nullable=False)
    is_bonus = db.Column(db.Boolean, default=False)
    bonus_type = db.Column(db.String(50), nullable=True)

class UserBonus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    bonus_type = db.Column(db.String(50))
    claimed_date = db.Column(db.Date, default=date.today)

# --- INITIAL DATA (run once) ---
@app.before_first_request
def setup_data():
    db.create_all()
    # Create rewards for 7 days if not exists
    if Reward.query.count() == 0:
        for i in range(1, 8):
            db.session.add(Reward(day_number=i, coins=100 * i, is_bonus=False))
        db.session.add_all([
            Reward(is_bonus=True, bonus_type='watch_ad', coins=100),
            Reward(is_bonus=True, bonus_type='share_app', coins=200),
            Reward(is_bonus=True, bonus_type='rate_app', coins=300),
        ])
        db.session.commit()
    # Create a test user
    if not User.query.first():
        user = User(name='Jessica Parker', role='Realist', coins=2450, gems=12, current_streak=5)
        db.session.add(user)
        db.session.commit()

# --- ROUTES ---

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Return user details for top card"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        "id": user.id,
        "name": user.name,
        "role": user.role,
        "coins": user.coins,
        "gems": user.gems,
        "current_streak": user.current_streak,
        "next_reward_in": "12:45:30"  # static placeholder for demo
    })

@app.route('/daily-reward/<int:user_id>', methods=['GET'])
def get_daily_reward(user_id):
    """Get today's reward info"""
    user = User.query.get_or_404(user_id)
    next_day = (user.current_streak % 7) + 1
    reward = Reward.query.filter_by(day_number=next_day, is_bonus=False).first()
    return jsonify({
        "day_number": reward.day_number,
        "coins": reward.coins,
        "message": f"Claim {reward.coins} coins for Day {reward.day_number}"
    })

@app.route('/claim-reward/<int:user_id>', methods=['POST'])
def claim_reward(user_id):
    """Claim the daily reward"""
    user = User.query.get_or_404(user_id)
    today = date.today()

    if user.last_claim_date == today:
        return jsonify({"message": "You already claimed today's reward"}), 400

    next_day = (user.current_streak % 7) + 1
    reward = Reward.query.filter_by(day_number=next_day, is_bonus=False).first()

    user.coins += reward.coins
    user.current_streak += 1
    user.last_claim_date = today
    db.session.commit()

    return jsonify({
        "message": f"Reward claimed successfully!",
        "coins_added": reward.coins,
        "new_balance": user.coins,
        "current_streak": user.current_streak
    })

@app.route('/bonus/<int:user_id>/<bonus_type>', methods=['POST'])
def claim_bonus(user_id, bonus_type):
    """Claim a bonus reward (watch ad, share app, rate app)"""
    user = User.query.get_or_404(user_id)
    today = date.today()

    # Check if already claimed today
    claimed = UserBonus.query.filter_by(
        user_id=user.id,
        bonus_type=bonus_type,
        claimed_date=today
    ).first()

    if claimed:
        return jsonify({"message": f"You already claimed {bonus_type} bonus today"}), 400

    reward = Reward.query.filter_by(is_bonus=True, bonus_type=bonus_type).first()
    if not reward:
        return jsonify({"message": "Invalid bonus type"}), 404

    user.coins += reward.coins
    new_bonus = UserBonus(user_id=user.id, bonus_type=bonus_type)
    db.session.add(new_bonus)
    db.session.commit()

    return jsonify({
        "message": f"Bonus '{bonus_type}' claimed!",
        "coins_added": reward.coins,
        "new_balance": user.coins
    })

@app.route('/')
def index():
    return jsonify({
        "message": "Daily Rewards API is running 🚀",
        "routes": [
            "/user/<user_id>",
            "/daily-reward/<user_id>",
            "/claim-reward/<user_id>",
            "/bonus/<user_id>/<bonus_type>"
        ]
    })

# --- MAIN ---
if _name_ == '_main_':
    app.run(debug=True)