import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

# -----------------------------------
# إعدادات عامة
# -----------------------------------
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("8578181432:AAF-CBoRlheu-4vg21sfhQDMsBXz6xWkQ0o")

PRODUCT, NATIONALITY, ST_NST, SECTOR, SALARY, OBLIGATIONS, TENURE = range(7)

# -----------------------------------
# قاعدة البيانات
# -----------------------------------
RATES_DB = [
    {"product": "Watani 1", "nationality": "Saudi", "type": "ST", "sector": "Gov't", "min": 2000, "max": 2999, "rate": 0.0753},
    {"product": "Watani 1", "nationality": "Saudi", "type": "ST", "sector": "Gov't", "min": 3000, "max": 3999, "rate": 0.0747},
    {"product": "Watani 1", "nationality": "Saudi", "type": "ST", "sector": "Gov't", "min": 4000, "max": 4999, "rate": 0.0741},
    {"product": "Watani 1", "nationality": "Saudi", "type": "ST", "sector": "Gov't", "min": 5000, "max": 5999, "rate": 0.0408},
    {"product": "Watani 1", "nationality": "Saudi", "type": "ST", "sector": "Gov't", "min": 6000, "max": 200000, "rate": 0.035},
    {"product": "Watani 2", "nationality": "Saudi", "type": "NST", "sector": "Pvt-C", "min": 10000, "max": 11999, "rate": 0.104},
    {"product": "Watani 2", "nationality": "Saudi", "type": "NST", "sector": "Pvt-C", "min": 12000, "max": 14999, "rate": 0.104},
    {"product": "Watani 2", "nationality": "Saudi", "type": "NST", "sector": "Pvt-C", "min": 15000, "max": 19999, "rate": 0.0995},
    {"product": "Watani 2", "nationality": "Saudi", "type": "NST", "sector": "Pvt-C", "min": 20000, "max": 24999, "rate": 0.0995},
    {"product": "Watani 1", "nationality": "Saudi", "type": "NST", "sector": "Military", "min": 2000, "max": 9999, "rate": 0.085},
    {"product": "Watani 1", "nationality": "Saudi", "type": "NST", "sector": "Military", "min": 10000, "max": 11999, "rate": 0.077},
    {"product": "Watani 1", "nationality": "Saudi", "type": "NST", "sector": "Military", "min": 12000, "max": 50000, "rate": 0.075},
]

# -----------------------------------
# دوال الحساب
# -----------------------------------
def get_rate(product, nationality, st_nst, sector, salary):
    for r in RATES_DB:
        if (
            r["product"] == product
            and r["nationality"] == nationality
            and r["type"] == st_nst
            and r["sector"] == sector
            and r["min"] <= salary <= r["max"]
        ):
            return r["rate"]

    if sector == "Gov't":
        return 0.035
    if sector == "Military":
        return 0.077
    if sector == "Pvt-C":
        return 0.104
    return 0.055


def calculate_finance(salary, obligations, tenure, rate, dbr=33.33):
    max_installment = (salary * (dbr / 100)) - obligations
    if max_installment <= 0:
        return 0, 0, 0, 0, rate

    installment = max_installment
    total = installment * tenure
    years = tenure / 12
    principal = total / (1 + (rate * years))
    profit = total - principal
    return principal, installment, total, profit, rate


# -----------------------------------
# خطوات البوت
# -----------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["Watani 1", "Watani 2"]]
    await update.message.reply_text(
        "👋 أهلاً بك في حاسبة التمويل\nاختر المنتج:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True),
    )
    return PRODUCT


async def product_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["product"] = update.message.text
    kb = [["Saudi"]]
    await update.message.reply_text("اختر الجنسية:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return NATIONALITY


async def nationality_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nationality"] = update.message.text
    kb = [["ST", "NST"]]
    await update.message.reply_text("نوع التحويل:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return ST_NST


async def type_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["st_nst"] = update.message.text
    kb = [["Gov't", "Military"], ["Pvt-C"]]
    await update.message.reply_text("اختر القطاع:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return SECTOR


async def sector_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sector"] = update.message.text
    await update.message.reply_text("أدخل صافي الراتب:", reply_markup=ReplyKeyboardRemove())
    return SALARY


async def salary_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["salary"] = float(update.message.text)
        await update.message.reply_text("أدخل الالتزامات الشهرية:")
        return OBLIGATIONS
    except ValueError:
        await update.message.reply_text("أدخل رقم صحيح.")
        return SALARY


async def obligations_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["obligations"] = float(update.message.text)
        await update.message.reply_text("مدة التمويل بالأشهر:")
        return TENURE
    except ValueError:
        await update.message.reply_text("أدخل رقم صحيح.")
        return OBLIGATIONS


async def tenure_step(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tenure = int(update.message.text)
        d = context.user_data
        rate = get_rate(d["product"], d["nationality"], d["st_nst"], d["sector"], d["salary"])
        principal, inst, total, profit, used_rate = calculate_finance(
            d["salary"], d["obligations"], tenure, rate
        )

        if principal == 0:
            await update.message.reply_text("❌ لا يوجد أهلية تمويل.")
        else:
            msg = (
                f"✅ ملخص التمويل\n"
                f"التمويل: {principal:,.2f} ريال\n"
                f"القسط: {inst:,.2f} ريال\n"
                f"النسبة: {used_rate*100:.2f}%\n"
                f"الإجمالي: {total:,.2f} ريال\n"
                f"الربح: {profit:,.2f} ريال\n\n"
                f"/start لحساب جديد"
            )
            await update.message.reply_text(msg)

        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("أدخل رقم صحيح.")
        return TENURE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# -----------------------------------
# التشغيل
# -----------------------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_step)],
            NATIONALITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, nationality_step)],
            ST_NST: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_step)],
            SECTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, sector_step)],
            SALARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, salary_step)],
            OBLIGATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, obligations_step)],
            TENURE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tenure_step)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()
