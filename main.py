from iqoptionapi.stable_api import IQ_Option
import time
import math

EMAIL = "boomzb168@gmail.com"
PASSWORD = "0936302614k"

print("กำลังเชื่อมต่อระบบ IQ Option...")
api = IQ_Option(EMAIL, PASSWORD)
check, reason = api.connect()

if check:
    print("✅ เชื่อมต่อสำเร็จ!")
    api.change_balance("PRACTICE")
    time.sleep(1)
    
    # ---------------------------------------------------------
    # ตั้งค่าเงื่อนไขการเทรด
    # ---------------------------------------------------------
    ASSET = "EURUSD-OTC"       # คู่เงิน (ตลาด OTC)
    TIMEFRAME_MINUTES = 1      # เลือกกรอบเวลาเทรด: 1 หรือ 5 นาที
    
    BASE_AMOUNT_THB = 350      # จำนวนเงินตั้งต้นไม้ที่ 1 (บาทไทย)
    EXCHANGE_RATE = 35.0       # อัตราแลกเปลี่ยน (บาทต่อ USD)
    
    MAX_MARTINGALE_STEPS = 3   # จำกัด Martingale สูงสุด 3 ไม้
    martingale_step = 1        # ตัวนับไม้ปัจจุบันเริ่มต้นที่ไม้ 1
    
    # ตัวแปรสำหรับเก็บสถิติ Win / Loss
    total_wins = 0
    total_losses = 0
    
    if TIMEFRAME_MINUTES not in [1, 5]:
        print("❌ Error: รองรับเฉพาะกรอบเวลา 1 นาที หรือ 5 นาที เท่านั้น!")
    else:
        if TIMEFRAME_MINUTES == 1:
            large_candle_period = 300  # เช็ค Sideway จากแท่ง 5 นาที (30 แท่ง)
        else:
            large_candle_period = 600  # เช็ค Sideway จากแท่ง 10 นาที (30 แท่ง)

        trade_candle_period = TIMEFRAME_MINUTES * 60 

        print(f"🚀 เริ่มต้นระบบบอทเทรดอัตโนมัติ | คู่เงิน: {ASSET} | กรอบเวลาเทรด: {TIMEFRAME_MINUTES} นาที")
        print(f"🧠 ระบบวิเคราะห์แบบจับคู่ (MA+RSI, BB+Stoch, MACD+ADX) + ไซส์เวย์ + Martingale พร้อมทำงาน!\n")

        while True:
            if martingale_step > MAX_MARTINGALE_STEPS:
                print(f"\n🛑 [STOP] แพ้ติดต่อกันครบ {MAX_MARTINGALE_STEPS} ไม้แล้ว! บอทหยุดทำงานเพื่อความปลอดภัยตามเงื่อนไข")
                break

            current_balance = api.get_balance()
            current_balance_thb = current_balance * EXCHANGE_RATE
            print(f"💼 [ยอดเงินในพอร์ตตอนนี้]: ${round(current_balance, 2)} (ประมาณ {round(current_balance_thb, 2)} บาท)")

            period_seconds = TIMEFRAME_MINUTES * 60
            server_time = api.get_server_timestamp()
            sleep_time = period_seconds - (server_time % period_seconds)
            
            print(f"⏳ กำลังรอเปิดแท่งเทียนใหม่... (อีกประมาณ {sleep_time} วินาที)")
            time.sleep(sleep_time + 2)

            print(f"\n-----------------------------------------")
            print(f"🔄 เริ่มรอบการวิเคราะห์แท่งใหม่ (Martingale ไม้ที่ {martingale_step}/{MAX_MARTINGALE_STEPS})")
            
            # 1. เช็ค Sideway จากแท่งใหญ่
            candles_large = api.get_candles(ASSET, large_candle_period, 30, time.time())
            is_sideway = False
            
            if candles_large and len(candles_large) >= 30:
                closes_l = [c.get('close', 0) for c in candles_large]
                opens_l = [c.get('open', 0) for c in candles_large]
                green_count = sum(1 for c, o in zip(closes_l, opens_l) if c > o)
                red_count = sum(1 for c, o in zip(closes_l, opens_l) if c < o)
                
                print(f"📊 ผลวิเคราะห์แท่งใหญ่ (30 แท่ง): เขียว = {green_count} | แดง = {red_count}")
                if 10 <= green_count <= 20 and 10 <= red_count <= 20:
                    is_sideway = True
                    print(f"🟢 ตลาดใหญ่เป็น 'ไซส์เวย์ (Sideway)' - ผ่านเกณฑ์!")
                else:
                    print(f"🔴 ตลาดไม่อยู่ในช่วงไซส์เวย์ (ข้ามรอบนี้)")
            else:
                print("⚠️ ไม่สามารถดึงข้อมูลแท่งเทียนใหญ่ได้")

            # 2. ถ้ายืนยันว่าเป็น Sideway นำแท่งเทียนจริงมาคำนวณการจับคู่อินดิเคเตอร์
            action = None
            if is_sideway:
                candles_trade = api.get_candles(ASSET, trade_candle_period, 50, time.time())
                if candles_trade and len(candles_trade) >= 35:
                    closes = [c.get('close', 0) for c in candles_trade]
                    opens = [c.get('open', 0) for c in candles_trade]
                    highs = [c.get('max', c.get('high', c.get('close', 0))) for c in candles_trade]
                    lows = [c.get('min', c.get('low', c.get('close', 0))) for c in candles_trade]

                    # --- สถานะแท่งก่อนหน้า ---
                    last_closed_trade_candle = candles_trade[-2]
                    prev_open = last_closed_trade_candle.get('open', 0)
                    prev_close = last_closed_trade_candle.get('close', 0)
                    prev_signal = "call" if prev_close < prev_open else "put"
                    print(f"📈 [แท่งก่อนหน้า]: ปิดเป็น {'สีแดง ➡️ [CALL]' if prev_signal == 'call' else 'สีเขียว ➡️ [PUT]'}")

                    # --- คู่ที่ 1: MA + RSI ---
                    ema9 = sum(closes[-9:]) / 9
                    ema21 = sum(closes[-21:]) / 21
                    ma_sig = "call" if ema9 > ema21 else "put"

                    gains, losses = [], []
                    for i in range(1, len(closes)):
                        diff = closes[i] - closes[i-1]
                        gains.append(diff if diff > 0 else 0)
                        losses.append(abs(diff) if diff < 0 else 0)
                    avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else 1
                    avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else 1
                    rsi = 100 if avg_loss == 0 else 100 - (100 / (1 + (avg_gain / avg_loss)))
                    rsi_sig = "call" if rsi <= 30 else ("put" if rsi >= 70 else ("call" if rsi < 50 else "put"))
                    
                    # คู่ MA + RSI ต้องสอดคล้องกัน ถึงจะได้ 1 คะแนนโหวตคู่นี้
                    pair1_sig = ma_sig if ma_sig == rsi_sig else None
                    print(f"🔗 [คู่ที่ 1: MA + RSI] ➡️ ผลลัพธ์: {str(pair1_sig).upper() if pair1_sig else 'สัญญาณขัดแย้ง (Neutral)'}")

                    # --- คู่ที่ 2: Bollinger Bands + Stochastics ---
                    bb_sma = sum(closes[-20:]) / 20
                    variance = sum((x - bb_sma) ** 2 for x in closes[-20:]) / 20
                    std_dev = math.sqrt(variance) if variance > 0 else 0.0001
                    upper_band = bb_sma + (2 * std_dev)
                    lower_band = bb_sma - (2 * std_dev)
                    bb_sig = "call" if closes[-1] <= lower_band else ("put" if closes[-1] >= upper_band else ("call" if closes[-1] < bb_sma else "put"))

                    h_14 = max(highs[-14:]) if len(highs) >= 14 else highs[-1]
                    l_14 = min(lows[-14:]) if len(lows) >= 14 else lows[-1]
                    stoch_k = 50 if h_14 == l_14 else ((closes[-1] - l_14) / (h_14 - l_14)) * 100
                    stoch_sig = "call" if stoch_k <= 20 else ("put" if stoch_k >= 80 else ("call" if stoch_k < 50 else "put"))

                    pair2_sig = bb_sig if bb_sig == stoch_sig else None
                    print(f"🔗 [คู่ที่ 2: BB + Stoch] ➡️ ผลลัพธ์: {str(pair2_sig).upper() if pair2_sig else 'สัญญาณขัดแย้ง (Neutral)'}")

                    # --- คู่ที่ 3: MACD + ADX ---
                    ema12 = sum(closes[-12:]) / 12
                    ema26 = sum(closes[-26:]) / 26
                    macd_line = ema12 - ema26
                    macd_signal_line = macd_line * 0.9
                    macd_sig = "call" if macd_line > macd_signal_line else "put"

                    trs, plus_dms, minus_dms = [], [], []
                    for i in range(1, len(closes)):
                        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
                        trs.append(tr)
                        up_move = highs[i] - highs[i-1]
                        down_move = lows[i-1] - lows[i]
                        plus_dms.append(up_move if (up_move > down_move and up_move > 0) else 0)
                        minus_dms.append(down_move if (down_move > up_move and down_move > 0) else 0)
                    
                    if len(trs) >= 14:
                        atr_val = sum(trs[-14:]) / 14
                        sum_pdm = sum(plus_dms[-14:])
                        sum_mdm = sum(minus_dms[-14:])
                        plus_di = (sum_pdm / atr_val) * 100 if atr_val > 0 else 0
                        minus_di = (sum_mdm / atr_val) * 100 if atr_val > 0 else 0
                        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100 if (plus_di + minus_di) > 0 else 0
                        adx_sig = "call" if plus_di > minus_di else "put"
                    else:
                        dx = 0
                        adx_sig = "call"

                    # MACD และ ADX ต้องสอดคล้องกัน
                    pair3_sig = macd_sig if (dx >= 20 and macd_sig == adx_sig) else None
                    print(f"🔗 [คู่ที่ 3: MACD + ADX] ➡️ ผลลัพธ์: {str(pair3_sig).upper() if pair3_sig else 'สัญญาณขัดแย้ง/ตลาดไร้เทรนด์ (Neutral)'}")

                    # --- รวมคะแนนการตัดสินใจ ---
                    # นำสัญญาณจากคู่หลักทั้ง 3 และแท่งก่อนหน้ามารวมกัน
                    active_signals = [prev_signal]
                    if pair1_sig: active_signals.append(pair1_sig)
                    if pair2_sig: active_signals.append(pair2_sig)
                    if pair3_sig: active_signals.append(pair3_sig)

                    call_votes = active_signals.count("call")
                    put_votes = active_signals.count("put")

                    print(f"📊 [สรุปคะแนนคู่หลัก]: [CALL = {call_votes} เสียง] | [PUT = {put_votes} เสียง]")

                    # เงื่อนไข: ต้องมีเสียงเห็นพ้องตั้งแต่ 3 เสียงขึ้นไป (จากคู่ที่จับคู่สำเร็จ + แท่งก่อนหน้า)
                    if call_votes >= 3:
                        action = "call"
                        print(f"📈 [ระบบสรุปผล]: คู่สัญญาณจับมือกันผ่านเกณฑ์ ➡️ ออกออเดอร์: [CALL (ซื้อขึ้น)]")
                    elif put_votes >= 3:
                        action = "put"
                        print(f"📉 [ระบบสรุปผล]: คู่สัญญาณจับมือกันผ่านเกณฑ์ ➡️ ออกออเดอร์: [PUT (ซื้อลง)]")
                    else:
                        print("⚠️ คู่สัญญาณขัดแย้งกันเอง ไม่ถึงเกณฑ์ (งดเทรดรอบนี้)")
                else:
                    print("⚠️ ข้อมูลแท่งเทียนไม่พอคำนวณคู่สัญญาณ")

            # 3. ทำการเปิดออเดอร์
            if is_sideway and action:
                multiplier = 2 ** (martingale_step - 1)
                amount_thb = BASE_AMOUNT_THB * multiplier
                amount_usd = round(max(1.0, amount_thb / EXCHANGE_RATE), 2)

                print(f"🎯 [ส่งคำสั่ง] ไม้ที่ {martingale_step} | ลงทุน {amount_thb} บาท (${amount_usd}) | ทิศทาง: {action.upper()}")

                balance_before = api.get_balance()
                check_order, order_id = api.buy(amount_usd, ASSET, action, TIMEFRAME_MINUTES)

                if check_order:
                    print(f"✅ เปิดออเดอร์สำเร็จ! Order ID: {order_id}")
                    print(f"⏳ กำลังรอผลการเทรด {TIMEFRAME_MINUTES} นาที...")
                    
                    time.sleep(TIMEFRAME_MINUTES * 60 + 6)
                    
                    balance_after = api.get_balance()
                    balance_diff = balance_after - balance_before
                    
                    if balance_diff > 0:
                        total_wins += 1
                        profit_thb = balance_diff * EXCHANGE_RATE
                        print(f"🎉 [WIN] ชนะการเทรด! ได้กำไรสุทธิ +${round(balance_diff, 2)} (ประมาณ +{round(profit_thb, 2)} บาท)")
                        martingale_step = 1  
                    else:
                        total_losses += 1
                        print(f"❌ [LOSS] แพ้การเทรด! ไม้นี้เสียเงินลงทุนไป")
                        martingale_step += 1 

                    total_trades = total_wins + total_losses
                    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
                    print(f"📊 [สถิติรวม] ชนะ: {total_wins} ไม้ | แพ้: {total_losses} ไม้ | รวมทั้งหมด: {total_trades} ไม้ | Win Rate: {round(win_rate, 2)}%")
                else:
                    print(f"❌ เปิดออเดอร์ไม่สำเร็จ เนื่องจาก: {order_id}")
            else:
                print("🛑 ข้ามรอบนี้เนื่องจากกราฟไม่เข้าเงื่อนไขหรือสัญญาณคู่ไม่ตรงกัน รอรอบถัดไป...")
                
            print(f"-----------------------------------------\n")
            time.sleep(3)

else:
    print(f"❌ เชื่อมต่อไม่สำเร็จ: {reason}")
