(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const num = (id, fallback = 0) => {
    const el = document.getElementById(id);
    const value = el ? Number(el.value) : fallback;
    return Number.isFinite(value) ? value : fallback;
  };

  /* ---------- 移动端导航 ---------- */
  const menuToggle = $('#menu-toggle');
  const sideNav = $('#side-nav');
  const closeNav = () => {
    if (!sideNav || !menuToggle) return;
    sideNav.classList.remove('is-open');
    menuToggle.setAttribute('aria-expanded', 'false');
  };
  if (menuToggle && sideNav) {
    menuToggle.addEventListener('click', () => {
      const open = sideNav.classList.toggle('is-open');
      menuToggle.setAttribute('aria-expanded', String(open));
    });
    $$('#side-nav a').forEach((link) => link.addEventListener('click', closeNav));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeNav();
    });
  }

  /* ---------- 滚动定位当前章节 ---------- */
  const navLinks = $$('.nav-link');
  const sections = $$('main section[id]');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        navLinks.forEach((link) => link.classList.toggle('is-active', link.getAttribute('href') === `#${entry.target.id}`));
      });
    }, { rootMargin: '-22% 0px -62% 0px', threshold: 0.01 });
    sections.forEach((section) => observer.observe(section));
  }

  /* ---------- 代码地图 ---------- */
  const codeFiles = [
    { name: 'config.h', layer: '配置', group: '应用', role: '把所有可调参数集中在一个入口。', necessity: '删掉后所有模块找不到参数，工程无法编译。', tech: 'C 宏定义', key: 'CFG_*' },
    { name: 'user_app.c / .h', layer: '应用入口', group: '应用', role: '初始化模块、启动三个串口接收中断、运行主循环。', necessity: '删掉后没有初始化和主循环。', tech: 'HAL UART 中断 + 回调', key: 'User_Init / User_Loop' },
    { name: 'bsp_bluetooth.c / .h', layer: '协议', group: '协议', role: '收发 AA55 二进制帧，逐字节解析并校验。', necessity: '删掉后蓝牙无法控制，也看不到遥测。', tech: '状态机 + 校验和 + UART', key: 'Bluetooth_OnRxByte' },
    { name: 'control_mode.c / .h', layer: '控制决策', group: '算法', role: '管理空闲、手动、位置控制、路线和旋转模式。', necessity: '删掉后没有控制逻辑，车不会响应模式。', tech: '状态机 + PID（仅测试页） + 遥测', key: 'ControlMode_Poll' },
    { name: 'chassis_control.c / .h', layer: '运动学', group: '算法', role: '把车体 vx/vy/wz 换算成 A/B/C/D 四轮线速度。', necessity: '删掉后没有全向移动能力。', tech: '麦轮逆运动学 / 正运动学', key: 'Chassis_Inverse' },
    { name: 'bsp_motor.c / .h', layer: '执行器', group: '硬件', role: '把四轮目标速度限幅到 -1~1，再调用驱动通信。', necessity: '删掉后电机收不到目标速度。', tech: '限幅 + 文本协议', key: 'Motor_SetSpeed' },
    { name: 'bsp_encoder.c / .h', layer: '传感器', group: '硬件', role: '把编码器计数换算成速度、距离，并维护软件零点。', necessity: '删掉后没有速度/距离反馈，PID 无法工作。', tech: '计数换算 + 零点', key: 'Encoder_GetWheelSpeeds' },
    { name: 'driver_comm.c / .h', layer: '驱动通信', group: '协议', role: '发送 $Car、请求编码器/电压，解析模块文本回包。', necessity: '删掉后 STM32 与驱动模块断开。', tech: 'UART + sscanf + 字符串格式化', key: 'DriverComm_SendCar' },
    { name: 'pid.c / .h', layer: '算法', group: '算法', role: '位置式 PID，带积分限幅和输出限幅。', necessity: '删掉后位置精准停无法闭环。', tech: 'P/I/D + 积分抗饱和', key: 'PID_Compute' },
    { name: 'route.c / .h', layer: '路线', group: '算法', role: '固件路线接口；当前是占位实现。', necessity: '删掉后 0x05 无处理；PC 路线仍可用。', tech: '状态机占位', key: 'Route_Start / Route_Poll' },
    { name: 'main.c', layer: 'CubeMX 入口', group: '应用', role: 'HAL 初始化、168MHz 时钟、调用 User_Init/User_Loop。', necessity: '删掉后程序没有入口。', tech: 'HAL + RCC/PLL', key: 'main / SystemClock_Config' },
    { name: 'usart.c', layer: 'CubeMX 初始化', group: '硬件', role: '初始化 USART1/2/3 和 GPIO 复用、NVIC。', necessity: '删掉后三个串口都不能用。', tech: 'HAL UART + GPIO AF', key: 'MX_USART*_UART_Init' },
    { name: 'protocol.py', layer: '上位机协议', group: '上位机', role: '组帧、解析回包、构造所有指令。', necessity: '删掉后 UI 无法和 STM32 通信。', tech: 'struct + 状态机', key: 'build_frame / FrameParser' },
    { name: 'serial_worker.py', layer: '上位机通信', group: '上位机', role: '在后台线程读写串口，避免界面卡顿。', necessity: '删掉后 UI 没有串口通道。', tech: 'QThread + pyserial', key: 'SerialWorker' },
    { name: 'ui/main_window.py', layer: '上位机界面', group: '上位机', role: '手动遥控、路线、PID、曲线、调试中心和日志。', necessity: '删掉后没有可操作界面。', tech: 'PySide6 + pyqtgraph', key: 'MainWindow' },
    { name: 'demo_worker.py', layer: '演示模式', group: '上位机', role: '没有硬件时模拟状态和曲线。', necessity: '删掉后演示模式无法使用。', tech: '定时模拟 + 协议数据', key: 'DemoWorker' },
    { name: 'test_app.c', layer: '测试工程', group: '算法', role: '解析 ASCII 命令，做单轮、CPR、旋转、PID 仿真。', necessity: '删掉后测试和标定入口消失。', tech: '命令行解析 + 直接调用硬件层', key: 'Test_ProcessLine' },
    { name: 'debug_algo.c / .h', layer: '测试算法', group: '算法', role: '不碰硬件的纯算法：麦轮、CPR、旋转时间。', necessity: '删掉后测试工程失去算法预览。', tech: '纯 C 计算函数', key: 'DebugAlgo_SuggestCpr' }
  ];

  const codeGrid = $('#code-grid');
  const renderCode = (filter = '全部') => {
    if (!codeGrid) return;
    const list = filter === '全部' ? codeFiles : codeFiles.filter((file) => file.group === filter);
    codeGrid.innerHTML = list.map((file) => `
      <article class="code-card">
        <div class="code-card-top"><span class="code-layer">${file.layer}</span><span>${file.group}</span></div>
        <h3>${file.name}</h3>
        <p>${file.role}</p>
        <p class="necessity">${file.necessity}</p>
        <footer><span>${file.tech}</span><code>${file.key}</code></footer>
      </article>
    `).join('');
  };
  renderCode();
  $$('.filter-button').forEach((button) => {
    button.addEventListener('click', () => {
      $$('.filter-button').forEach((item) => item.classList.remove('is-active'));
      button.classList.add('is-active');
      renderCode(button.dataset.codeFilter);
    });
  });

  /* ---------- 参数中心 ---------- */
  const parameters = [
    { name: 'CFG_BLUETOOTH_BAUD', value: '9600', unit: 'bps', impact: 'USART1 与 HC-04 的通信速率', fail: '不对则完全无数据或乱码', algo: false },
    { name: 'CFG_DRIVER_BAUD', value: '115200', unit: 'bps', impact: '注释上的驱动模块波特率', fail: '当前 usart.c 仍硬编码，改宏不一定生效', algo: false },
    { name: 'CFG_DEBUG_BAUD', value: '115200', unit: 'bps', impact: '注释上的调试波特率', fail: '当前 usart.c 仍硬编码', algo: false },
    { name: 'CFG_WHEEL_DIAMETER_MM', value: '80.0', unit: 'mm', impact: '轮速、距离和模块轮径参数', fail: '偏大或偏小会让距离比例错', algo: true },
    { name: 'CFG_WHEELBASE_MM', value: '130.0', unit: 'mm', impact: '麦轮逆运动学的半轴距', fail: '旋转和横移的轮速差不对', algo: true },
    { name: 'CFG_TRACK_MM', value: '123.5', unit: 'mm', impact: '麦轮逆运动学的半轮距', fail: '旋转和横移的轮速差不对', algo: true },
    { name: 'CFG_ENCODER_CPR', value: '2464.0', unit: 'counts/rev', impact: '计数→圈数→速度/距离', fail: '速度、距离、PID 全比例错', algo: true },
    { name: 'CFG_MAX_SPEED_M_S', value: '1.0', unit: 'm/s', impact: '手动 vx/vy 限幅', fail: '太大失控，太小很肉', algo: true },
    { name: 'CFG_MAX_OMEGA_RAD_S', value: '1.0', unit: 'rad/s', impact: '手动 wz 限幅', fail: '旋转过快或打滑', algo: true },
    { name: 'CFG_MAX_WHEEL_SPEED_M_S', value: '1.0', unit: 'm/s', impact: '轮速归一化到 -1~1', fail: '归一化比例错，实际速度偏大/偏小', algo: true },
    { name: 'CFG_MIN_DRIVE', value: '0.30', unit: 'normalized', impact: '低速最小驱动缩放', fail: '太小震动，太大起步猛', algo: true },
    { name: 'CFG_ROTATE_DRIVE', value: '0.60', unit: 'normalized', impact: '原地旋转轮速', fail: '太小不转/震动，太大过冲', algo: true },
    { name: 'CFG_ROTATE_MS_PER_90', value: '900', unit: 'ms', impact: '时间控制旋转角度', fail: '角度偏大或偏小', algo: true },
    { name: 'CFG_ROTATE_TOL_DEG', value: '2.0', unit: '°', impact: '注释上的旋转到位容差', fail: '当前未实际使用', algo: true },
    { name: 'CFG_YAW_SIGN', value: '1.0', unit: '—', impact: '注释上的偏航方向', fail: '当前未实际使用', algo: true },
    { name: 'CFG_DEBUG_BRIDGE_ENABLE', value: '1', unit: '—', impact: '是否从 USART3 镜像协议帧', fail: '0 会关闭有线镜像', algo: false },
    { name: 'CFG_LOOP_MS', value: '20', unit: 'ms', impact: '控制主循环周期', fail: '改小更快，但更吃 CPU/串口', algo: true },
    { name: 'CFG_TELEMETRY_MS', value: '100', unit: 'ms', impact: '状态/曲线上报周期', fail: '改小曲线更密，串口压力更大', algo: false },
    { name: 'CFG_POS_KP', value: '0.8', unit: '—', impact: '位置环比例', fail: '大→更快但可能超调', algo: true },
    { name: 'CFG_POS_KI', value: '0.0', unit: '—', impact: '位置环积分', fail: '大→消静差但可能振荡', algo: true },
    { name: 'CFG_POS_KD', value: '0.0', unit: '—', impact: '位置环微分', fail: '大→阻尼但可能放大噪声', algo: true },
    { name: 'CFG_ROUTE_SIDE_MM', value: '800', unit: 'mm', impact: '注释上的路线边长', fail: '当前 PC 路线不一定使用', algo: true },
    { name: 'POS_STOP_TOL_MM', value: '10.0', unit: 'mm', impact: '位置停到位容差', fail: '太大停不准，太小来回找', algo: true },
    { name: 'SERIAL_BAUDRATE', value: '9600', unit: 'bps', impact: '上位机默认蓝牙串口速率', fail: '与固件不一致则无数据', algo: false },
    { name: 'TX_INTERVAL_MS', value: '50', unit: 'ms', impact: '上位机手动发送周期', fail: '太小可能堵塞，太大操控延迟', algo: false }
  ];

  const paramBody = $('#param-body');
  const paramSearch = $('#param-search');
  const paramCount = $('#param-count');
  const renderParams = (query = '') => {
    if (!paramBody) return;
    const q = query.trim().toLowerCase();
    const list = parameters.filter((item) => {
      const haystack = `${item.name} ${item.value} ${item.unit} ${item.impact} ${item.fail}`.toLowerCase();
      return !q || haystack.includes(q);
    });
    paramBody.innerHTML = list.map((item) => `
      <tr>
        <td>${item.algo ? '<span class="algo-badge inline">算法</span> ' : ''}${item.name}</td>
        <td>${item.value}</td>
        <td>${item.unit}</td>
        <td>${item.impact}</td>
        <td>${item.fail}</td>
      </tr>
    `).join('');
    if (paramCount) paramCount.textContent = q ? `匹配 ${list.length} / ${parameters.length} 项` : `显示全部 ${parameters.length} 项`;
  };
  renderParams();
  if (paramSearch) paramSearch.addEventListener('input', () => renderParams(paramSearch.value));

  /* ---------- 标定计算器 ---------- */
  const CAL_KEY = 'mecanum-lab-calibration-v1';
  const calIds = ['cal-counts', 'cal-distance', 'cal-diameter', 'cal-current-cpr', 'cal-measured', 'cal-current-ms'];
  const calInputs = calIds.map((id) => document.getElementById(id)).filter(Boolean);

  const format = (value, digits = 1) => Number.isFinite(value) ? value.toFixed(digits) : '—';

  const calculateCalibration = () => {
    const counts = Math.abs(num('cal-counts'));
    const distance = num('cal-distance');
    const diameter = num('cal-diameter');
    const currentCpr = num('cal-current-cpr');
    const measured = num('cal-measured');
    const currentMs = num('cal-current-ms');

    const circumference = Math.PI * diameter / 1000;
    const rev = distance > 0 ? (distance / 1000) / circumference : 0;
    const suggestedCpr = rev > 0.0001 && counts > 0 ? counts / rev : 0;
    const suggestedMs = measured > 0.1 && currentMs > 0 ? currentMs * 90 / measured : 0;

    const cprStrong = $('#cpr-result strong');
    const cprSmall = $('#cpr-result small');
    if (cprStrong) cprStrong.textContent = suggestedCpr > 0 ? suggestedCpr.toFixed(0) : '—';
    if (cprSmall) {
      const delta = suggestedCpr > 0 && currentCpr > 0 ? ((suggestedCpr - currentCpr) / currentCpr) * 100 : NaN;
      cprSmall.textContent = suggestedCpr > 0 ? `相对当前 ${delta >= 0 ? '+' : ''}${format(delta, 2)}%` : '等待有效输入';
    }

    const rotStrong = $('#rotate-result strong');
    const rotSmall = $('#rotate-result small');
    if (rotStrong) rotStrong.textContent = suggestedMs > 0 ? suggestedMs.toFixed(0) : '—';
    if (rotSmall) {
      rotSmall.textContent = suggestedMs > 0 ? `实测 ${format(measured, 1)}° → 目标 90°` : '等待有效输入';
    }

    try {
      localStorage.setItem(CAL_KEY, JSON.stringify({ counts, distance, diameter, currentCpr, measured, currentMs }));
    } catch (error) { /* 本地文件模式下可能禁用存储，忽略即可 */ }
  };

  try {
    const saved = JSON.parse(localStorage.getItem(CAL_KEY) || 'null');
    if (saved && typeof saved === 'object') {
      const values = [saved.counts, saved.distance, saved.diameter, saved.currentCpr, saved.measured, saved.currentMs];
      calInputs.forEach((input, index) => { if (Number.isFinite(values[index])) input.value = values[index]; });
    }
  } catch (error) { /* 忽略损坏的本地记录 */ }
  calInputs.forEach((input) => input.addEventListener('input', calculateCalibration));
  calculateCalibration();

  /* ---------- 麦轮运动学 ---------- */
  const kinIds = ['kin-vx', 'kin-vy', 'kin-wz'];
  const kinInputs = kinIds.map((id) => document.getElementById(id)).filter(Boolean);
  const kinWheels = ['a', 'b', 'c', 'd'].map((name) => document.getElementById(`wheel-${name}`)).filter(Boolean);

  const updateKinematics = () => {
    const vx = num('kin-vx');
    const vy = num('kin-vy');
    const wz = num('kin-wz');
    const lw = 130 / 2000 + 123.5 / 2000;
    const wheelMps = [vx - vy - lw * wz, vx + vy + lw * wz, vx + vy - lw * wz, vx - vy + lw * wz];
    const normalized = wheelMps.map((value) => clamp(value / 1.0, -1, 1));

    ['kin-vx', 'kin-vy', 'kin-wz'].forEach((id) => {
      const out = document.getElementById(`${id}-out`);
      if (out) out.textContent = num(id).toFixed(2);
    });

    kinWheels.forEach((group, index) => {
      const value = normalized[index];
      const text = group.querySelector('.wheel-value');
      if (text) text.textContent = value.toFixed(2);
      group.classList.toggle('is-positive', value > 0.002);
      group.classList.toggle('is-negative', value < -0.002);
    });

    const bars = $('#wheel-bars');
    if (bars) {
      bars.innerHTML = ['A', 'B', 'C', 'D'].map((name, index) => {
        const value = normalized[index];
        return `<div class="wheel-bar ${value < 0 ? 'is-negative' : ''}"><span>${name}</span><b>${value.toFixed(2)}</b><i style="--fill:${Math.abs(value) * 100}%"></i></div>`;
      }).join('');
    }

    const arrow = $('#motion-arrow');
    if (arrow) {
      const x = 260 - vy * 66;
      const y = 166 - vx * 66;
      arrow.setAttribute('d', `M260 166 L${x.toFixed(1)} ${y.toFixed(1)}`);
      arrow.style.opacity = Math.abs(vx) + Math.abs(vy) > 0.01 ? '1' : '0';
    }
  };
  kinInputs.forEach((input) => input.addEventListener('input', updateKinematics));
  updateKinematics();

  /* ---------- PID 模拟器 ---------- */
  const pidCanvas = $('#pid-chart');
  const pidStats = $('#pid-stats');
  const pidInputs = ['pid-kp', 'pid-ki', 'pid-kd', 'pid-target'].map((id) => document.getElementById(id)).filter(Boolean);

  const drawPidChart = (series, targetMm) => {
    if (!pidCanvas) return;
    const ctx = pidCanvas.getContext('2d');
    const width = pidCanvas.width;
    const height = pidCanvas.height;
    const pad = { left: 58, right: 22, top: 24, bottom: 38 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;
    const maxY = Math.max(targetMm * 1.25, Math.max(...series, 1) * 1.15, 10);
    const points = series.length;
    const x = (index) => pad.left + (index / Math.max(points - 1, 1)) * plotW;
    const y = (value) => pad.top + plotH - (clamp(value, 0, maxY) / maxY) * plotH;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0c1117';
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = '#1f2b35';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i += 1) {
      const gy = pad.top + (plotH / 5) * i;
      ctx.beginPath();
      ctx.moveTo(pad.left, gy);
      ctx.lineTo(width - pad.right, gy);
      ctx.stroke();
    }
    for (let i = 0; i <= 5; i += 1) {
      const gx = pad.left + (plotW / 5) * i;
      ctx.beginPath();
      ctx.moveTo(gx, pad.top);
      ctx.lineTo(gx, height - pad.bottom);
      ctx.stroke();
    }

    ctx.fillStyle = '#6c7c88';
    ctx.font = '12px Cascadia Mono, Consolas, monospace';
    ctx.fillText('mm', 15, pad.top + 4);
    ctx.fillText('0', pad.left - 10, height - pad.bottom + 17);
    ctx.fillText(String(Math.round(maxY)), 15, pad.top + 5);
    ctx.fillText('t / s', width - pad.right - 32, height - 8);

    ctx.setLineDash([6, 6]);
    ctx.strokeStyle = '#5cd6d0';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(pad.left, y(targetMm));
    ctx.lineTo(width - pad.right, y(targetMm));
    ctx.stroke();
    ctx.setLineDash([]);

    const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + plotH);
    gradient.addColorStop(0, 'rgba(255, 180, 92, .25)');
    gradient.addColorStop(1, 'rgba(255, 180, 92, 0)');
    ctx.beginPath();
    ctx.moveTo(x(0), y(series[0]));
    series.forEach((value, index) => ctx.lineTo(x(index), y(value)));
    ctx.lineTo(x(series.length - 1), pad.top + plotH);
    ctx.lineTo(x(0), pad.top + plotH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    ctx.beginPath();
    ctx.strokeStyle = '#ffb45c';
    ctx.lineWidth = 2;
    series.forEach((value, index) => {
      if (index === 0) ctx.moveTo(x(index), y(value));
      else ctx.lineTo(x(index), y(value));
    });
    ctx.stroke();
  };

  const runPid = () => {
    const kp = num('pid-kp');
    const ki = num('pid-ki');
    const kd = num('pid-kd');
    const targetMm = num('pid-target', 500);
    const dt = 0.02;
    const steps = 500;
    const target = targetMm / 1000;
    let position = 0;
    let velocity = 0;
    let integral = 0;
    let previousError = 0;
    const series = [];

    for (let i = 0; i < steps; i += 1) {
      const error = target - position;
      integral = clamp(integral + error * dt, -1, 1);
      const derivative = error - previousError;
      let command = kp * error + ki * integral + kd * derivative;
      command = clamp(command, -1.4, 1.4);
      velocity += (command - velocity) * 0.14;
      position += velocity * dt;
      series.push(position * 1000);
      previousError = error;
    }

    drawPidChart(series, targetMm);

    const finalError = Math.abs(targetMm - series[series.length - 1]);
    const overshoot = Math.max(0, Math.max(...series) - targetMm);
    let lastOutside = -1;
    series.forEach((value, index) => { if (Math.abs(value - targetMm) > 5) lastOutside = index; });
    const settle = lastOutside >= 0 ? ((lastOutside + 1) * dt).toFixed(2) : '0.00';
    if (pidStats) {
      pidStats.innerHTML = `<span>最终误差 <strong>${finalError.toFixed(1)} mm</strong></span><span>超调 <strong>${overshoot.toFixed(1)} mm</strong></span><span>进入 ±5mm 时间 <strong>${settle} s</strong></span>`;
    }
  };

  const syncPidLabels = () => {
    ['pid-kp', 'pid-ki', 'pid-kd', 'pid-target'].forEach((id) => {
      const out = document.getElementById(`${id}-out`);
      if (out) out.textContent = id === 'pid-target' ? String(Math.round(num(id))) : num(id).toFixed(2);
    });
  };
  pidInputs.forEach((input) => input.addEventListener('input', () => {
    syncPidLabels();
    runPid();
  }));
  syncPidLabels();
  runPid();
  const pidRun = $('#pid-run');
  if (pidRun) pidRun.addEventListener('click', runPid);
  const pidReset = $('#pid-reset');
  if (pidReset) pidReset.addEventListener('click', () => {
    const defaults = { 'pid-kp': 0.8, 'pid-ki': 0, 'pid-kd': 0, 'pid-target': 500 };
    Object.entries(defaults).forEach(([id, value]) => { const el = document.getElementById(id); if (el) el.value = value; });
    syncPidLabels();
    runPid();
  });

  /* ---------- 协议实验室 ---------- */
  const commandMeta = {
    manual: { cmd: 0x01, name: '手动速度' },
    'brake-fast': { cmd: 0x02, name: '急刹停' },
    'pid-stop': { cmd: 0x04, name: '位置 PID 停' },
    rotate: { cmd: 0x0d, name: '原地旋转' },
    heartbeat: { cmd: 0x0a, name: '心跳' },
    stop: { cmd: 0x06, name: '急停' },
  };

  const fieldMarkup = {
    manual: `<label>vx / m/s<input id="proto-vx" type="number" step="0.01" value="1.0" inputmode="decimal"></label><label>vy / m/s<input id="proto-vy" type="number" step="0.01" value="0" inputmode="decimal"></label><label>wz / rad/s<input id="proto-wz" type="number" step="0.01" value="0" inputmode="decimal"></label>`,
    'pid-stop': `<label>目标距离 / mm<input id="proto-mm" type="number" step="1" value="500" inputmode="numeric"></label>`,
    rotate: `<label>旋转角度 / °<input id="proto-angle" type="number" step="1" value="90" inputmode="decimal"></label><small>正数左转，负数右转；发送单位为 0.1°。</small>`,
    'brake-fast': `<p class="form-note">该指令没有数据字段。</p>`,
    heartbeat: `<p class="form-note">该指令没有数据字段；发送后期待 ACK。</p>`,
    stop: `<p class="form-note">该指令没有数据字段；立即停车并清目标。</p>`
  };

  const protoFields = $('#proto-fields');
  const protoCommand = $('#proto-command');
  const renderProtoFields = () => {
    if (!protoFields || !protoCommand) return;
    protoFields.innerHTML = fieldMarkup[protoCommand.value] || '';
    buildProtocolFrame();
  };

  const int16LE = (value) => {
    const v = Math.max(-32768, Math.min(32767, Math.round(value)));
    return [v & 0xff, (v >> 8) & 0xff];
  };
  const uint16LE = (value) => {
    const v = Math.max(0, Math.min(65535, Math.round(value)));
    return [v & 0xff, (v >> 8) & 0xff];
  };
  const checksum = (bytes) => bytes.reduce((sum, value) => (sum + value) & 0xff, 0);
  const buildFrame = (cmd, data) => {
    const len = 1 + data.length;
    return [0xaa, 0x55, len, cmd, ...data, checksum([len, cmd, ...data])];
  };
  const toHex = (bytes) => bytes.map((value) => value.toString(16).padStart(2, '0').toUpperCase()).join(' ');

  function readProtocolData(command) {
    if (command === 'manual') return [...int16LE(num('proto-vx') * 1000), ...int16LE(num('proto-vy') * 1000), ...int16LE(num('proto-wz') * 1000)];
    if (command === 'pid-stop') return int16LE(num('proto-mm'));
    if (command === 'rotate') return int16LE(num('proto-angle') * 10);
    return [];
  }

  function buildProtocolFrame() {
    if (!protoCommand) return;
    const command = protoCommand.value;
    const meta = commandMeta[command];
    const data = readProtocolData(command);
    const frame = buildFrame(meta.cmd, data);
    const output = $('#proto-output');
    if (output) output.textContent = toHex(frame);
  }

  if (protoCommand) {
    protoCommand.addEventListener('change', renderProtoFields);
    renderProtoFields();
  }
  const protoBuild = $('#proto-build');
  if (protoBuild) protoBuild.addEventListener('click', buildProtocolFrame);
  const protoPreset = $('#proto-preset');
  if (protoPreset) protoPreset.addEventListener('click', () => {
    if (!protoCommand) return;
    protoCommand.value = 'manual';
    renderProtoFields();
    const values = { 'proto-vx': 1.0, 'proto-vy': 0, 'proto-wz': 0 };
    Object.entries(values).forEach(([id, value]) => { const el = document.getElementById(id); if (el) el.value = value; });
    buildProtocolFrame();
  });
  const protoCopy = $('#proto-copy');
  if (protoCopy) protoCopy.addEventListener('click', async () => {
    const output = $('#proto-output');
    if (!output) return;
    try {
      await navigator.clipboard.writeText(output.textContent);
      protoCopy.textContent = '已复制';
      setTimeout(() => { protoCopy.textContent = '复制十六进制'; }, 1400);
    } catch (error) {
      const range = document.createRange();
      range.selectNodeContents(output);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
  });

  function parseProtocolFrame() {
    const input = $('#proto-input');
    const result = $('#proto-parse-result');
    if (!input || !result) return;
    const clean = input.value.trim().replace(/0x/gi, '').replace(/[^0-9a-f]/gi, '');
    if (clean.length < 10 || clean.length % 2 !== 0) {
      result.innerHTML = '<span class="bad">不是完整的十六进制字节串。</span>';
      return;
    }
    const bytes = [];
    for (let i = 0; i < clean.length; i += 2) bytes.push(parseInt(clean.slice(i, i + 2), 16));
    const start = bytes.findIndex((value, index) => value === 0xaa && bytes[index + 1] === 0x55);
    if (start < 0 || bytes.length < start + 4) {
      result.innerHTML = '<span class="bad">找不到 AA 55 帧头。</span>';
      return;
    }
    const len = bytes[start + 2];
    const frameLength = len + 4;
    if (len < 1 || bytes.length < start + frameLength) {
      result.innerHTML = '<span class="bad">长度字段与实际字节数不匹配。</span>';
      return;
    }
    const body = bytes.slice(start + 3, start + 3 + len);
    const cmd = body[0];
    const data = body.slice(1);
    const received = bytes[start + 3 + len];
    const expected = checksum([len, cmd, ...data]);
    const ok = received === expected;
    const meta = Object.values(commandMeta).find((item) => item.cmd === cmd);
    let decoded = '';
    if (cmd === 0x01 && data.length >= 6) {
      const read16 = (offset) => {
        const raw = data[offset] | (data[offset + 1] << 8);
        return raw > 32767 ? raw - 65536 : raw;
      };
      decoded = `vx=${(read16(0) / 1000).toFixed(3)} m/s，vy=${(read16(2) / 1000).toFixed(3)} m/s，wz=${(read16(4) / 1000).toFixed(3)} rad/s`;
    } else if (cmd === 0x0d && data.length >= 2) {
      const raw = data[0] | (data[1] << 8);
      const signed = raw > 32767 ? raw - 65536 : raw;
      decoded = `角度=${(signed / 10).toFixed(1)}°`;
    } else if (cmd === 0x04 && data.length >= 2) {
      const raw = data[0] | (data[1] << 8);
      const signed = raw > 32767 ? raw - 65536 : raw;
      decoded = `目标距离=${signed} mm`;
    }
    result.innerHTML = `
      <strong>${ok ? '校验通过' : '校验失败'}</strong> · ${meta ? meta.name : `未知指令 0x${cmd.toString(16).toUpperCase()}`}
      <dl>
        <dt>LEN</dt><dd>${len}</dd>
        <dt>CMD</dt><dd>0x${cmd.toString(16).toUpperCase().padStart(2, '0')}</dd>
        <dt>DATA</dt><dd>${data.length ? data.map((value) => value.toString(16).toUpperCase().padStart(2, '0')).join(' ') : '（无）'}</dd>
        <dt>CHECK</dt><dd>收到 0x${received.toString(16).toUpperCase().padStart(2, '0')} / 计算 0x${expected.toString(16).toUpperCase().padStart(2, '0')}</dd>
        ${decoded ? `<dt>解码</dt><dd>${decoded}</dd>` : ''}
      </dl>
    `;
  }
  const protoParse = $('#proto-parse');
  if (protoParse) protoParse.addEventListener('click', parseProtocolFrame);

  /* ---------- 故障排查 ---------- */
  const troubles = [
    { title: '蓝牙显示连接，但没有 RX 数据', summary: '链路/端口/波特率', checks: ['确认 COM7/COM8 方向与软件打开的口一致', '确认 USART1 与 HC-04 都是 9600', '确认 TX/RX 交叉、GND 共地', '用 COM5 有线链路对照是否有 0x81'] },
    { title: '电机完全不转', summary: '电源/驱动/指令', checks: ['驱动模块 12V 是否上电', '电机插头是否插紧', '是否处于 IDLE 或被急停覆盖', '单轮 wheel 命令能否转动'] },
    { title: '轮子震动、转一下停一下', summary: '低速/电流/编码器', checks: ['提高 CFG_MIN_DRIVE 观察', '检查电源电压是否跌落', '检查编码器是否丢脉冲', '检查机械卡滞和轮子安装'] },
    { title: '编码器为 0 或方向相反', summary: 'A/B 相/供电/符号', checks: ['检查编码器 6P 插头', '检查 Vcc/GND/A/B', '手动转轮看计数正负', '区分编码器反向和电机反向'] },
    { title: '前进斜行、横移不对、旋转方向错', summary: '轮序/辊轮/几何', checks: ['确认 A/B/C/D 与实车位置', '确认左右辊轮镜像', '确认轴距 130mm、轮距 123.5mm', '逐轮检查正方向'] },
    { title: '固定路线刚开始就跳到第三条边', summary: '定时器/状态同步', checks: ['检查路线是否被重复启动', '检查 route_gen 是否作废旧定时器', '确认步骤在动作完成后推进', '低速、短边、长停顿复测'] },
    { title: 'PID 停超调或来回摆', summary: 'Kp/Ki/Kd/机械', checks: ['先降 Kp', '少量加 Kd', '确认积分没有饱和', '检查编码器计数和机械间隙'] },
    { title: 'Keil 无法编译或烧录', summary: '工具链/ST-Link/Flash', checks: ['确认 AC6 编译器', '检查头文件路径', '检查 ST-Link 和 SWD 接线', '检查 Flash Download 算法'] }
  ];
  const troubleList = $('#trouble-list');
  if (troubleList) {
    troubleList.innerHTML = troubles.map((item, index) => `
      <details class="trouble-item" ${index === 0 ? 'open' : ''}>
        <summary><span>0${index + 1}</span>${item.title}<small>${item.summary}</small></summary>
        <div class="trouble-body">${item.checks.map((check) => `<p><b>检查</b>${check}</p>`).join('')}</div>
      </details>
    `).join('');
  }

  /* ---------- 页面加载完成后的轻量初始化 ---------- */
  document.documentElement.classList.add('is-ready');
})();


