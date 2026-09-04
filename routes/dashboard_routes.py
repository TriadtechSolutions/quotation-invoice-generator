"""
Dashboard Route Blueprint
"""
from flask import Blueprint, render_template
from services.firebase_service import FirebaseService

dashboard_bp = Blueprint('dashboard', __name__)
fb_service = FirebaseService()


@dashboard_bp.route('/')
def index():
    recent_q = fb_service.get_all_quotations()[:5]
    recent_inv = fb_service.get_all_invoices()[:5]
    return render_template('dashboard.html', recent_quotations=recent_q, recent_invoices=recent_inv)
