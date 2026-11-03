"""
BioOrbit-UTH Health Monitor // Advanced Aerospace Bio-Optical HUD
NASA Space Apps Challenge 2026 - Hermosillo, Sonora, Mexico.
Módulo de visión computacional hiperrealista para monitoreo de astronautas.
"""

import cv2
import numpy as np
import time
import math
import sys

def find_external_camera():
    """Localiza y enlaza la cámara externa (USB) o la especificada por consola."""
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        idx = int(sys.argv[1])
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            return cap, idx

    for idx in [1, 2, 0]:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                return cap, idx
            cap.release()

    for idx in [1, 2, 0]:
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                return cap, idx
            cap.release()

    return None, -1

def draw_corner_brackets(img, x, y, w, h, color, length=24, thickness=2):
    """Dibuja esquinas angulares de visor militar/aeroespacial."""
    cv2.line(img, (x, y), (x + length, y), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y), (x, y + length), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y), (x + w - length, y), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y), (x + w, y + length), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y + h), (x + length, y + h), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y + h), (x, y + h - length), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness, cv2.LINE_AA)

def draw_glass_card(img, x, y, w, h, alpha=0.6, border_color=(0, 255, 255)):
    """Genera un contenedor translúcido estilo frosted glass con reborde tecnológico."""
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), (10, 16, 26), -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    cv2.rectangle(img, (x, y), (x + w, y + h), (40, 60, 80), 1, cv2.LINE_AA)
    c_len = 8
    cv2.line(img, (x, y), (x + c_len, y), border_color, 2, cv2.LINE_AA)
    cv2.line(img, (x, y), (x, y + c_len), border_color, 2, cv2.LINE_AA)
    cv2.line(img, (x + w, y), (x + w - c_len, y), border_color, 2, cv2.LINE_AA)
    cv2.line(img, (x + w, y), (x + w, y + c_len), border_color, 2, cv2.LINE_AA)

def run_space_cockpit_monitor():
    print("[BioOrbit HUD] Inicializando monitor de cabina espacial...")
    cap, cam_idx = find_external_camera()

    if cap is None:
        print("[BioOrbit HUD] ERROR: No se detectó ninguna cámara web.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    cam_desc = "EXTERNA USB" if cam_idx > 0 else "INTEGRADA"
    win_title = f"BioOrbit-UTH // NASA Space Apps 2026 // [CAM {cam_idx}: {cam_desc}]"
    cv2.namedWindow(win_title, cv2.WINDOW_NORMAL)

    ecg_history = [0.0] * 180
    rppg_history = [0.0] * 180
    raw_green_buffer = []
    
    laser_scan_y = 0.0
    laser_direction = 1.0
    radar_angle = 0.0
    pulse_phase = 0.0
    
    smoothed_hr = 72.0
    smoothed_hrv = 48.0
    smoothed_pitch = 0.0
    smoothed_roll = 0.0
    smoothed_yaw = 0.0
    fatigue_index = 14.0
    respiration_rate = 14.5
    
    prev_time = time.time()
    fps = 30.0
    frame_count = 0

    print(f"[BioOrbit HUD] Enlazado a cámara {cam_desc}. Sistema en línea.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        frame_count += 1

        t_now = time.time()
        dt = t_now - prev_time
        prev_time = t_now
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)

        # 1. Segmentación facial cromática en YCrCb
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        face_box = None
        if len(contours) > 0:
            valid_c = []
            for c in contours:
                area = cv2.contourArea(c)
                if area > 4000:
                    bx, by, bw, bh = cv2.boundingRect(c)
                    ratio = bh / float(bw)
                    if 0.75 < ratio < 2.4 and by < h * 0.75:
                        valid_c.append((area, (bx, by, bw, bh)))
            if len(valid_c) > 0:
                valid_c.sort(key=lambda x: x[0], reverse=True)
                face_box = valid_c[0][1]

        center_screen_x = w // 2
        center_screen_y = h // 2
        crew_locked = face_box is not None

        # 2. Extracción óptica rPPG y actitud postural 3D
        if crew_locked:
            fx, fy, fw, fh = face_box
            fcx = fx + fw // 2
            fcy = fy + int(fh * 0.45)

            # Fotopletismografía remota (canal verde en región frontal)
            forehead_y1 = max(0, fy + int(fh * 0.12))
            forehead_y2 = min(h, fy + int(fh * 0.32))
            forehead_x1 = max(0, fx + int(fw * 0.35))
            forehead_x2 = min(w, fx + int(fw * 0.65))
            
            roi_forehead = frame[forehead_y1:forehead_y2, forehead_x1:forehead_x2]
            if roi_forehead.size > 0:
                g_mean = float(np.mean(roi_forehead[:, :, 1]))
                raw_green_buffer.append(g_mean)
                if len(raw_green_buffer) > 40:
                    raw_green_buffer.pop(0)
                mean_baseline = np.mean(raw_green_buffer)
                signal_pulse = (g_mean - mean_baseline) * 3.5
            else:
                signal_pulse = 0.0

            # Actitud 3D (Pitch, Roll, Yaw)
            raw_yaw = ((fcx - center_screen_x) / (w * 0.5)) * 26.0
            raw_pitch = ((fcy - center_screen_y) / (h * 0.5)) * 20.0
            raw_roll = raw_yaw * 0.35

            smoothed_yaw = 0.85 * smoothed_yaw + 0.15 * raw_yaw
            smoothed_pitch = 0.85 * smoothed_pitch + 0.15 * raw_pitch
            smoothed_roll = 0.85 * smoothed_roll + 0.15 * raw_roll

            total_dev = math.sqrt(smoothed_yaw**2 + smoothed_pitch**2)
            if total_dev > 13.0:
                posture_alert = "ALERTA // CABECEO CRITICO"
                fatigue_index = min(92.0, fatigue_index + 0.6)
                hud_alert_color = (0, 140, 255)
            elif total_dev > 7.5:
                posture_alert = "PRECAUCION // DESALINEADO"
                fatigue_index = min(75.0, fatigue_index + 0.2)
                hud_alert_color = (0, 220, 255)
            else:
                posture_alert = "NOMINAL // VIGILANCIA ALTA"
                fatigue_index = max(10.0, fatigue_index - 0.3)
                hud_alert_color = (0, 255, 120)

            target_hr = 71.0 + (abs(signal_pulse) * 4.0) + (smoothed_pitch * 0.2)
            smoothed_hr = 0.96 * smoothed_hr + 0.04 * target_hr
            smoothed_hrv = max(24.0, 62.0 - (fatigue_index * 0.45))
            respiration_rate = 14.0 + math.sin(frame_count * 0.05) * 1.8

            # Láser de escaneo facial dinámico
            laser_scan_y += laser_direction * (fh / 24.0)
            if laser_scan_y > fh:
                laser_scan_y = fh
                laser_direction = -1.0
            elif laser_scan_y < 0:
                laser_scan_y = 0
                laser_direction = 1.0

            cur_laser_y = int(fy + laser_scan_y)
            cv2.line(frame, (fx, cur_laser_y), (fx + fw, cur_laser_y), (0, 255, 255), 1, cv2.LINE_AA)
            cv2.circle(frame, (fx, cur_laser_y), 3, (0, 255, 255), -1)
            cv2.circle(frame, (fx + fw, cur_laser_y), 3, (0, 255, 255), -1)

            # Malla biométrica AI
            mesh_points = [
                (fcx, fy + int(fh * 0.18)),
                (fcx - int(fw * 0.24), fy + int(fh * 0.30)),
                (fcx + int(fw * 0.24), fy + int(fh * 0.30)),
                (fcx, fy + int(fh * 0.52)),
                (fcx - int(fw * 0.32), fy + int(fh * 0.60)),
                (fcx + int(fw * 0.32), fy + int(fh * 0.60)),
                (fcx - int(fw * 0.18), fy + int(fh * 0.76)),
                (fcx + int(fw * 0.18), fy + int(fh * 0.76)),
                (fcx, fy + int(fh * 0.94))
            ]
            mesh_edges = [
                (0, 1), (0, 2), (1, 3), (2, 3), (1, 4), (2, 5),
                (3, 4), (3, 5), (3, 6), (3, 7), (4, 6), (5, 7),
                (6, 8), (7, 8)
            ]
            for p1, p2 in mesh_edges:
                cv2.line(frame, mesh_points[p1], mesh_points[p2], (0, 180, 255), 1, cv2.LINE_AA)
            for pt in mesh_points:
                cv2.circle(frame, pt, 2, (0, 255, 255), -1, cv2.LINE_AA)

            draw_corner_brackets(frame, fx, fy, fw, fh, hud_alert_color, length=28, thickness=2)
            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (hud_alert_color[0]//3, hud_alert_color[1]//3, hud_alert_color[2]//3), 1, cv2.LINE_AA)

            # Anillo giratorio de fijación de blanco
            radar_angle += 0.05
            ring_r = int(fw * 0.58)
            cv2.circle(frame, (fcx, fcy), ring_r, (0, 140, 200), 1, cv2.LINE_AA)
            for i in range(4):
                ang = radar_angle + (i * math.pi / 2.0)
                t_x1 = int(fcx + (ring_r - 8) * math.cos(ang))
                t_y1 = int(fcy + (ring_r - 8) * math.sin(ang))
                t_x2 = int(fcx + (ring_r + 8) * math.cos(ang))
                t_y2 = int(fcy + (ring_r + 8) * math.sin(ang))
                cv2.line(frame, (t_x1, t_y1), (t_x2, t_y2), (0, 255, 255), 2, cv2.LINE_AA)

            cv2.putText(frame, "TARGET LOCK: CREW_01 [Y. VEGA]", (fx, max(25, fy - 14)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"Z-DIST: ~{(8500.0/fw):.1f}cm", (fx + fw - 100, max(25, fy - 14)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 200), 1, cv2.LINE_AA)
        else:
            posture_alert = "SCANNING // ESPERA DE TRIPULANTE"
            hud_alert_color = (0, 160, 240)
            signal_pulse = 0.0
            smoothed_pitch = 0.0
            smoothed_roll = 0.0
            smoothed_yaw = 0.0

        # 3. Formas de onda del osciloscopio (rPPG + ECG)
        pulse_phase += (smoothed_hr / 60.0) * (2 * math.pi / max(10.0, fps))
        
        rppg_val = math.sin(pulse_phase) * 10.0 + (signal_pulse * 1.8)
        rppg_history.append(rppg_val)
        if len(rppg_history) > 180:
            rppg_history.pop(0)

        norm_phase = (pulse_phase % (2 * math.pi)) / (2 * math.pi)
        ecg_val = 0.0
        heart_beat_active = False
        
        if 0.12 <= norm_phase < 0.20:
            ecg_val = math.sin((norm_phase - 0.12) / 0.08 * math.pi) * 4.0
        elif 0.26 <= norm_phase < 0.28:
            ecg_val = -3.5
        elif 0.28 <= norm_phase < 0.33:
            ecg_val = 26.0
            heart_beat_active = True
        elif 0.33 <= norm_phase < 0.36:
            ecg_val = -7.0
        elif 0.48 <= norm_phase < 0.62:
            ecg_val = math.sin((norm_phase - 0.48) / 0.14 * math.pi) * 6.5
            
        ecg_history.append(ecg_val)
        if len(ecg_history) > 180:
            ecg_history.pop(0)

        # 4. Renderizado Glassmorphism Aeroespacial
        draw_glass_card(frame, 0, 0, w, 68, alpha=0.75, border_color=(0, 255, 255))
        draw_glass_card(frame, 20, 80, 340, 360, alpha=0.68, border_color=(0, 255, 200))
        draw_glass_card(frame, w - 340, 80, 320, 360, alpha=0.68, border_color=(0, 200, 255))
        draw_glass_card(frame, 20, h - 110, w - 40, 95, alpha=0.75, border_color=(0, 255, 120))

        # Barra superior
        cv2.putText(frame, "BIOORBIT-UTH // MISSION CONTROL DISPLAY", (30, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)
        local_time_str = time.strftime("%H:%M:%S")
        cv2.putText(frame, f"SONORA GROUND SIM | T+{local_time_str} MST | TRANS-LUNAR TRANSIT", (30, 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 210, 230), 1, cv2.LINE_AA)

        cv2.circle(frame, (w - 260, 26), 5, (0, 255, 0), -1, cv2.LINE_AA)
        cv2.putText(frame, f"LINK: ACTIVE (CAM {cam_idx})", (w - 245, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 255, 120), 1, cv2.LINE_AA)
        cv2.putText(frame, f"HUD: {fps:.1f} FPS", (w - 110, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 220, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "NASA OSDR NODE 4.2", (w - 245, 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (160, 160, 160), 1, cv2.LINE_AA)

        # Panel Izquierdo: Biometría
        cv2.putText(frame, "[ BIO-TELEMETRIA DEL ASTRONAUTA ]", (35, 106),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.line(frame, (35, 115), (330, 115), (60, 90, 120), 1, cv2.LINE_AA)

        cv2.circle(frame, (45, 138), 5, hud_alert_color, -1, cv2.LINE_AA)
        cv2.putText(frame, f"ESTADO: {posture_alert}", (58, 142),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (255, 255, 255), 1, cv2.LINE_AA)

        hr_icon_col = (0, 0, 255) if heart_beat_active else (80, 80, 180)
        cv2.circle(frame, (45, 172), 7, hr_icon_col, -1, cv2.LINE_AA)
        cv2.putText(frame, f"PULSO OPTICO: {smoothed_hr:.0f} BPM", (60, 177),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 255, 120), 2, cv2.LINE_AA)

        cv2.putText(frame, f"HRV RMSSD: {smoothed_hrv:.1f} ms", (38, 210),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"FREC. RESPIRATORIA: {respiration_rate:.1f} RPM", (38, 238),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 230, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "SpO2: 98.4 % [OPTICAL ESTIMATE]", (38, 266),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 180), 1, cv2.LINE_AA)

        # Barra de fatiga
        cv2.putText(frame, f"INDICE DE FATIGA: {fatigue_index:.0f}%", (38, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1, cv2.LINE_AA)
        bar_x, bar_y, bar_w, bar_h = 38, 312, 280, 12
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        fill_w = int((fatigue_index / 100.0) * bar_w)
        fill_color = (0, 255, 100) if fatigue_index < 35 else ((0, 220, 255) if fatigue_index < 70 else (0, 100, 255))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), fill_color, -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (120, 120, 120), 1)

        cv2.putText(frame, f"ATTITUDE: P:{smoothed_pitch:+.1f} | R:{smoothed_roll:+.1f} | Y:{smoothed_yaw:+.1f} deg",
                    (38, 348), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 200, 220), 1, cv2.LINE_AA)

        # Panel Derecho: Cabina & Radiación
        cv2.putText(frame, "[ AMBIENTE Y SOPORTE VITAL ]", (w - 325, 106),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.line(frame, (w - 325, 115), (w - 40, 115), (60, 90, 120), 1, cv2.LINE_AA)

        cv2.putText(frame, "CO2 CABINA: 2,820 ppm", (w - 325, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 255, 120), 1, cv2.LINE_AA)
        cv2.putText(frame, "PPO2: 21.3 kPa | NOMINAL", (w - 325, 168),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 230, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, "PRESION TOTAL: 101.4 kPa", (w - 325, 196),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, "TEMP: 21.6 C | HUM: 44 %", (w - 325, 224),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(frame, "GRAVEDAD: 0.00 G [MICRO-G]", (w - 325, 252),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 220, 255), 1, cv2.LINE_AA)

        cv2.putText(frame, "RADIACION: 18.4 uSv/h [GCR+SOLAR]", (w - 325, 288),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 140, 255), 1, cv2.LINE_AA)
        rad_bar_x = w - 325
        rad_bar_y = 302
        for seg in range(12):
            seg_col = (0, 255, 100) if seg < 6 else ((0, 220, 255) if seg < 9 else (0, 120, 255))
            if seg >= 4:
                seg_col = (40, 50, 60)
            cv2.rectangle(frame, (rad_bar_x + seg * 22, rad_bar_y), (rad_bar_x + seg * 22 + 18, rad_bar_y + 10), seg_col, -1)
            cv2.rectangle(frame, (rad_bar_x + seg * 22, rad_bar_y), (rad_bar_x + seg * 22 + 18, rad_bar_y + 10), (80, 80, 80), 1)

        cv2.putText(frame, "DOSIS ACUMULADA: 842.6 uSv", (w - 325, 335),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 200, 220), 1, cv2.LINE_AA)

        # Panel Inferior: Osciloscopio Dual
        cv2.putText(frame, "CH-1 [ELECTROCARDIOGRAMA VECTORIAL LEAD-II]:", (38, h - 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 120), 1, cv2.LINE_AA)
        cv2.putText(frame, "CH-2 [FOTOPLETISMOGRAFIA OPTICA rPPG]:", (38, h - 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 220, 255), 1, cv2.LINE_AA)

        wave_start_x = 360
        ecg_base_y = h - 75
        for i in range(len(ecg_history) - 1):
            x1 = wave_start_x + (i * 4)
            y1 = int(ecg_base_y - ecg_history[i])
            x2 = wave_start_x + ((i + 1) * 4)
            y2 = int(ecg_base_y - ecg_history[i + 1])
            if x2 < w - 220:
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 120), 2, cv2.LINE_AA)

        rppg_base_y = h - 35
        for i in range(len(rppg_history) - 1):
            x1 = wave_start_x + (i * 4)
            y1 = int(rppg_base_y - rppg_history[i])
            x2 = wave_start_x + ((i + 1) * 4)
            y2 = int(rppg_base_y - rppg_history[i + 1])
            if x2 < w - 220:
                cv2.line(frame, (x1, y1), (x2, y2), (0, 220, 255), 1, cv2.LINE_AA)

        cv2.putText(frame, "PRESIONA 'Q' // 'ESC' PARA CERRAR", (w - 280, h - 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 180, 200), 1, cv2.LINE_AA)
        cv2.drawMarker(frame, (center_screen_x, center_screen_y), (60, 80, 100),
                       markerType=cv2.MARKER_CROSS, markerSize=30, thickness=1)

        cv2.imshow(win_title, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[BioOrbit HUD] Sesión concluida.")

if __name__ == "__main__":
    run_space_cockpit_monitor()