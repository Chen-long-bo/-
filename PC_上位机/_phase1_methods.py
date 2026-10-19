# -*- coding: utf-8 -*-
p = r"D:\CODEX-WORK\蓝牙遥控麦轮小车\PC_上位机\ui\main_window.py"
c = open(p, encoding="utf-8").read()

anchor = "    def _on_pid_stop(self):"
methods = '''    def _send_raw_frame(self):
        """发送输入的十六进制原始帧。"""
        text = self.edit_raw.text().replace(" ", "").replace(",", "")   # 去掉空格/逗号
        try:
            data = bytes.fromhex(text)                     # 转字节
        except ValueError:
            self._log("原始帧格式错误，请输入十六进制，如 AA 55 01 0A 0B")
            return
        if not (self.worker and self.connected):           # 未连接
            self._log("请先连接")
            return
        self.worker.send_frame(data)                       # 原样发送
        self._log(f"原始帧已发送: {data.hex(' ').upper()}")

    def _calib_record_start(self):
        """记录编码器标定起点。"""
        if not self.last_status:                           # 没有状态帧
            self._log("还没有收到编码器数据，先连接并等待状态帧")
            return
        self.calib_start_counts = list(self.last_status["enc"])   # 保存起点
        self._log(f"编码器起点: {self.calib_start_counts}")

    def _calib_compute_cpr(self):
        """根据实际距离计算建议 CPR。"""
        if not self.calib_start_counts or not self.last_status:   # 缺数据
            self._log("请先记录起点，并确认已收到终点状态帧")
            return
        end = self.last_status["enc"]                       # 终点计数
        deltas = [end[i] - self.calib_start_counts[i] for i in range(4)]   # 四轮差值
        avg = sum(deltas) / 4.0                             # 平均计数
        dist_m = self.spin_calib_mm.value() / 1000.0        # 实际距离 m
        circumference = math.pi * (config.WHEEL_DIAMETER_MM / 1000.0)   # 轮周长 m
        if dist_m <= 0.001:                                 # 距离太小
            self._log("实际距离太小，无法计算")
            return
        rev = dist_m / circumference                        # 输出轴转数
        suggested = abs(avg) / rev if rev > 0 else 0.0      # 建议 CPR
        self.lbl_calib_result.setText(f"建议 CPR: {suggested:.0f} counts/rev")
        self._log(f"CPR 标定: 平均计数={avg:.1f}, 距离={dist_m:.3f}m, 建议 CPR={suggested:.0f}")

    def _rotate_calib_send(self):
        """发送一次 90° 旋转，供用户测量实际角度。"""
        self._send(protocol.cmd_rotate(90))                 # 发送 90°
        self._log("已发送左转90°，请测量实际转过的角度后填写")

    def _rotate_calib_compute(self):
        """根据实测角度计算建议 90° 时间。"""
        measured = self.spin_calib_deg.value()              # 实测角度
        if measured <= 0.1:                                 # 角度太小
            self._log("实测角度必须大于 0")
            return
        suggested = config.ROTATE_MS_PER_90 * 90.0 / measured   # 按比例换算
        self.lbl_rot_result.setText(f"建议 90° 时间: {suggested:.0f} ms")
        self._log(f"旋转标定: 实测 {measured:.1f}°，建议 90° 时间 {suggested:.0f} ms")

    def _pulse_motion(self, vx, vy, wz, ms=600):
        """短脉冲运动：发一段速度，到时自动停。"""
        if not (self.worker and self.connected):            # 未连接
            self._log("请先连接")
            return
        self.manual_pause_until = time.time() + (ms / 1000.0) + 0.2   # 防止手动 tick 覆盖
        self._send(protocol.cmd_manual(vx, vy, wz))         # 发送速度
        QTimer.singleShot(ms, lambda: self._send(protocol.cmd_stop_all()))   # 到时停
        self._log(f"点动: vx={vx} vy={vy} wz={wz}，{ms}ms")

    def _geo_compute(self):
        """本地预览麦轮逆运动学的四轮速度。"""
        vx = self.spin_geo_vx.value()                       # 前后速度
        vy = self.spin_geo_vy.value()                       # 左右速度
        wz = self.spin_geo_wz.value()                       # 旋转速度
        a = config.WHEELBASE_MM / 2000.0                    # 半轴距 m
        b = config.TRACK_MM / 2000.0                        # 半轮距 m
        lw = a + b                                          # 几何参数
        w = [vx - vy - lw * wz,                             # A 左前
             vx + vy + lw * wz,                             # B 右前
             vx + vy - lw * wz,                             # C 左后
             vx - vy + lw * wz]                             # D 右后
        self.lbl_geo.setText("A/B/C/D: " + " / ".join(f"{x:.3f}" for x in w) + " m/s")
        self._log(f"几何预览: {self.lbl_geo.text()}")

    def _debug_accel_apply(self):
        """下发调试中心的加速度平滑参数。"""
        self._send(protocol.cmd_set_accel(self.spin_dbg_accel_v.value(),
                                          self.spin_dbg_accel_w.value()))
        self._log("调试中心：已下发加速度平滑参数")

'''
assert anchor in c
c = c.replace(anchor, methods + anchor, 1)
open(p, "w", encoding="utf-8").write(c)
print("debug methods inserted")
