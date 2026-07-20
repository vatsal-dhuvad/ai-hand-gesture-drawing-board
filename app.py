import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="AI Hand Gesture Drawing Board",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            color-scheme: light !important;
        }
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stHeader"] {
            background: #f3f6fb !important;
            color: #111827 !important;
        }
        h1, h2, h3, p, span, label {
            color: #111827 !important;
            opacity: 1 !important;
        }
        .title {
            font-size: 2.35rem;
            font-weight: 850;
            letter-spacing: 0;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            color: #4b5563 !important;
            font-size: 1rem;
            margin-bottom: 1rem;
        }
        .note {
            background: #e8f5ee;
            border: 1px solid #b8e2c8;
            border-radius: 8px;
            color: #14532d !important;
            padding: 0.9rem 1rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">AI Hand Gesture Drawing Board</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Draw in the air with your hand using live browser camera, MediaPipe Hands, and canvas drawing tools.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="note">This deploy version has no heavy Python camera packages. Click Start Camera, allow camera permission, and draw directly in the browser.</div>',
    unsafe_allow_html=True,
)

components.html(
    """
    <!doctype html>
    <html>
    <head>
      <script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"></script>
      <style>
        * { box-sizing: border-box; }
        body {
          margin: 0;
          font-family: Inter, Segoe UI, Arial, sans-serif;
          background: #f3f6fb;
          color: #111827;
        }
        .app {
          display: grid;
          grid-template-columns: 300px 1fr;
          gap: 16px;
          min-height: 820px;
        }
        .panel, .stage-wrap, .help {
          background: #ffffff;
          border: 1px solid #d8e0ec;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        }
        .panel {
          padding: 16px;
          height: fit-content;
        }
        .panel h2, .help h2 {
          margin: 0 0 12px;
          font-size: 20px;
        }
        .field { margin-bottom: 14px; }
        label {
          display: block;
          font-size: 14px;
          font-weight: 750;
          margin-bottom: 6px;
        }
        select, input[type="range"], button {
          width: 100%;
        }
        input[type="checkbox"] {
          width: auto;
          accent-color: #ef4444;
          margin-right: 8px;
        }
        select {
          height: 40px;
          border-radius: 8px;
          border: 1px solid #cbd5e1;
          padding: 0 10px;
          background: #fff;
          color: #111827;
          font-weight: 650;
        }
        input[type="range"] {
          accent-color: #ef4444;
        }
        button {
          height: 42px;
          border-radius: 8px;
          border: 1px solid #bfdbfe;
          background: #eff6ff;
          color: #1d4ed8;
          font-weight: 850;
          cursor: pointer;
          margin-bottom: 8px;
        }
        button.primary {
          background: #1d4ed8;
          color: #ffffff;
          border-color: #1d4ed8;
        }
        button.danger {
          background: #fef2f2;
          color: #b91c1c;
          border-color: #fecaca;
        }
        .status {
          margin-top: 10px;
          padding: 10px;
          border-radius: 8px;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          font-size: 14px;
          line-height: 1.45;
        }
        .stage-wrap {
          padding: 14px;
        }
        .stage {
          position: relative;
          width: 100%;
          aspect-ratio: 16 / 9;
          background: #111827;
          border-radius: 8px;
          overflow: hidden;
        }
        video, canvas {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
        }
        video { display: none; }
        .help {
          margin-top: 16px;
          padding: 16px;
        }
        .cards {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
        }
        .card {
          border: 1px solid #d8e0ec;
          border-radius: 8px;
          padding: 12px;
          min-height: 86px;
          background: #ffffff;
        }
        .card strong {
          display: block;
          margin-bottom: 4px;
        }
        .card span {
          color: #4b5563;
          font-size: 14px;
        }
        .swatches {
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          gap: 6px;
        }
        .swatch {
          height: 28px;
          border-radius: 8px;
          border: 2px solid #e5e7eb;
          cursor: pointer;
        }
        .swatch.active {
          border-color: #111827;
          outline: 2px solid #bfdbfe;
        }
        @media (max-width: 900px) {
          .app { grid-template-columns: 1fr; }
          .cards { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class="app">
        <aside class="panel">
          <h2>Controls</h2>

          <button id="startBtn" class="primary">Start Camera</button>
          <button id="stopBtn">Stop Camera</button>
          <button id="clearBtn" class="danger">Clear Canvas</button>
          <button id="undoBtn">Undo</button>
          <button id="saveBtn">Download Drawing</button>

          <div class="field">
            <label for="tool">Tool</label>
            <select id="tool">
              <option>Pencil</option>
              <option>Line</option>
              <option>Rectangle</option>
              <option>Circle</option>
              <option>Eraser</option>
            </select>
          </div>

          <div class="field">
            <label>
              <input id="gestureErase" type="checkbox" checked>
              5-finger temporary erase
            </label>
          </div>

          <div class="field">
            <label>Color</label>
            <div class="swatches" id="swatches"></div>
          </div>

          <div class="field">
            <label for="brush">Pencil / shape size: <span id="brushValue">8</span></label>
            <input id="brush" type="range" min="2" max="40" value="8">
          </div>

          <div class="field">
            <label for="eraser">Eraser size: <span id="eraserValue">55</span></label>
            <input id="eraser" type="range" min="20" max="140" value="55">
          </div>

          <div class="status">
            <strong>Status</strong><br>
            <span id="status">Camera stopped.</span><br>
            <span id="fingerStatus">Fingers: 0</span>
          </div>
        </aside>

        <main>
          <section class="stage-wrap">
            <div class="stage">
              <video id="video" playsinline></video>
              <canvas id="output"></canvas>
            </div>
          </section>

          <section class="help">
            <h2>Gesture Controls</h2>
            <div class="cards">
              <div class="card"><strong>1 finger</strong><span>Draw, erase, or preview selected shape.</span></div>
              <div class="card"><strong>2 fingers</strong><span>Move without drawing and finish shape.</span></div>
              <div class="card"><strong>3 fingers</strong><span>Change to next color.</span></div>
              <div class="card"><strong>4 fingers</strong><span>Change to the next tool.</span></div>
              <div class="card"><strong>5 fingers</strong><span>Erase with open hand.</span></div>
              <div class="card"><strong>Controls</strong><span>Pick tool, color, brush size, eraser size, undo, and download.</span></div>
            </div>
          </section>
        </main>
      </div>

      <script>
        const video = document.getElementById("video");
        const output = document.getElementById("output");
        const ctx = output.getContext("2d");
        const drawing = document.createElement("canvas");
        const dctx = drawing.getContext("2d");

        const startBtn = document.getElementById("startBtn");
        const stopBtn = document.getElementById("stopBtn");
        const clearBtn = document.getElementById("clearBtn");
        const undoBtn = document.getElementById("undoBtn");
        const saveBtn = document.getElementById("saveBtn");
        const toolInput = document.getElementById("tool");
        const gestureEraseInput = document.getElementById("gestureErase");
        const brushInput = document.getElementById("brush");
        const eraserInput = document.getElementById("eraser");
        const brushValue = document.getElementById("brushValue");
        const eraserValue = document.getElementById("eraserValue");
        const statusEl = document.getElementById("status");
        const fingerStatus = document.getElementById("fingerStatus");
        const swatches = document.getElementById("swatches");

        const colors = [
          { name: "Blue", value: "#1450ff" },
          { name: "Green", value: "#22c55e" },
          { name: "Red", value: "#ef4444" },
          { name: "Yellow", value: "#eab308" },
          { name: "Purple", value: "#a855f7" },
          { name: "White", value: "#ffffff" }
        ];

        let currentColorIndex = 0;
        let currentColor = colors[currentColorIndex].value;
        let previousPoint = null;
        let shapeStart = null;
        let shapeLast = null;
        let camera = null;
        let history = [];
        let colorCooldown = 0;
        let toolCooldown = 0;

        function setStatus(text) {
          statusEl.textContent = text;
        }

        function buildSwatches() {
          swatches.innerHTML = "";
          colors.forEach((color, index) => {
            const button = document.createElement("button");
            button.className = "swatch" + (index === currentColorIndex ? " active" : "");
            button.style.background = color.value;
            button.title = color.name;
            button.onclick = () => {
              currentColorIndex = index;
              currentColor = colors[index].value;
              buildSwatches();
            };
            swatches.appendChild(button);
          });
        }

        function resizeCanvases(width, height) {
          if (output.width === width && output.height === height) return;
          output.width = width;
          output.height = height;

          const oldDrawing = document.createElement("canvas");
          oldDrawing.width = drawing.width || width;
          oldDrawing.height = drawing.height || height;
          oldDrawing.getContext("2d").drawImage(drawing, 0, 0);

          drawing.width = width;
          drawing.height = height;
          dctx.drawImage(oldDrawing, 0, 0, width, height);
        }

        function pushHistory() {
          const snapshot = document.createElement("canvas");
          snapshot.width = drawing.width;
          snapshot.height = drawing.height;
          snapshot.getContext("2d").drawImage(drawing, 0, 0);
          history.push(snapshot);
          if (history.length > 20) history.shift();
        }

        function undo() {
          const snapshot = history.pop();
          if (!snapshot) return;
          dctx.clearRect(0, 0, drawing.width, drawing.height);
          dctx.drawImage(snapshot, 0, 0);
        }

        function isFingerOpen(landmarks, tip, pip) {
          return landmarks[tip].y < landmarks[pip].y;
        }

        function countFingers(landmarks, handedness) {
          let count = 0;
          const thumbOpen = handedness === "Right"
            ? landmarks[4].x < landmarks[3].x
            : landmarks[4].x > landmarks[3].x;
          if (thumbOpen) count++;
          if (isFingerOpen(landmarks, 8, 6)) count++;
          if (isFingerOpen(landmarks, 12, 10)) count++;
          if (isFingerOpen(landmarks, 16, 14)) count++;
          if (isFingerOpen(landmarks, 20, 18)) count++;
          return count;
        }

        function pointFromLandmark(landmark) {
          return {
            x: output.width - landmark.x * output.width,
            y: landmark.y * output.height
          };
        }

        function drawShape(targetCtx, tool, start, end, preview = false) {
          if (!start || !end) return;
          targetCtx.save();
          targetCtx.strokeStyle = currentColor;
          targetCtx.lineWidth = Number(brushInput.value);
          targetCtx.lineCap = "round";
          targetCtx.lineJoin = "round";
          if (preview) targetCtx.globalAlpha = 0.8;

          targetCtx.beginPath();
          if (tool === "Line") {
            targetCtx.moveTo(start.x, start.y);
            targetCtx.lineTo(end.x, end.y);
          } else if (tool === "Rectangle") {
            targetCtx.rect(start.x, start.y, end.x - start.x, end.y - start.y);
          } else if (tool === "Circle") {
            const radius = Math.hypot(end.x - start.x, end.y - start.y);
            targetCtx.arc(start.x, start.y, radius, 0, Math.PI * 2);
          }
          targetCtx.stroke();
          targetCtx.restore();
        }

        function drawFreehand(point, tool) {
          if (!previousPoint) {
            pushHistory();
            previousPoint = point;
          }

          dctx.save();
          dctx.lineCap = "round";
          dctx.lineJoin = "round";
          if (tool === "Eraser") {
            dctx.globalCompositeOperation = "destination-out";
            dctx.lineWidth = Number(eraserInput.value);
          } else {
            dctx.globalCompositeOperation = "source-over";
            dctx.strokeStyle = currentColor;
            dctx.lineWidth = Number(brushInput.value);
          }
          dctx.beginPath();
          dctx.moveTo(previousPoint.x, previousPoint.y);
          dctx.lineTo(point.x, point.y);
          dctx.stroke();
          dctx.restore();
          previousPoint = point;
        }

        function clearCanvas(saveUndo = true) {
          if (saveUndo) pushHistory();
          dctx.clearRect(0, 0, drawing.width, drawing.height);
          previousPoint = null;
          shapeStart = null;
          shapeLast = null;
        }

        function drawOverlay(results, fingers) {
          ctx.fillStyle = "rgba(17, 24, 39, 0.88)";
          ctx.fillRect(0, 0, output.width, 82);
          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 24px Arial";
          ctx.fillText("AI Hand Gesture Drawing Board", 18, 32);
          ctx.font = "15px Arial";
          const visibleTool = fingers === 5 && gestureEraseInput.checked ? "Temporary Eraser" : toolInput.value;
          ctx.fillText(`Tool: ${visibleTool} | Color: ${colors[currentColorIndex].name} | Brush: ${brushInput.value} | Eraser: ${eraserInput.value} | Fingers: ${fingers}`, 18, 60);

          if (results.multiHandLandmarks && results.multiHandLandmarks.length) {
            const landmarks = results.multiHandLandmarks[0].map(p => ({ x: 1 - p.x, y: p.y, z: p.z }));
            window.drawConnectors(ctx, landmarks, window.HAND_CONNECTIONS, { color: "#22c55e", lineWidth: 2 });
            window.drawLandmarks(ctx, landmarks, { color: "#ef4444", lineWidth: 1, radius: 3 });
          }
        }

        function onResults(results) {
          const width = video.videoWidth || 960;
          const height = video.videoHeight || 540;
          resizeCanvases(width, height);

          ctx.save();
          ctx.clearRect(0, 0, output.width, output.height);
          ctx.scale(-1, 1);
          ctx.drawImage(results.image, -output.width, 0, output.width, output.height);
          ctx.restore();

          let fingers = 0;
          if (results.multiHandLandmarks && results.multiHandLandmarks.length) {
            const landmarks = results.multiHandLandmarks[0];
            const handedness = results.multiHandedness?.[0]?.label || "Right";
            fingers = countFingers(landmarks, handedness);
            const point = pointFromLandmark(landmarks[8]);
            const tool = toolInput.value;

            if (colorCooldown > 0) colorCooldown--;
            if (toolCooldown > 0) toolCooldown--;
            if (fingers === 1) {
              if (["Line", "Rectangle", "Circle"].includes(tool)) {
                if (!shapeStart) {
                  pushHistory();
                  shapeStart = point;
                }
                shapeLast = point;
              } else {
                drawFreehand(point, tool);
              }
            } else if (fingers === 2) {
              previousPoint = null;
              if (shapeStart && shapeLast && ["Line", "Rectangle", "Circle"].includes(tool)) {
                drawShape(dctx, tool, shapeStart, shapeLast);
              }
              shapeStart = null;
              shapeLast = null;
            } else if (fingers === 3 && colorCooldown === 0) {
              currentColorIndex = (currentColorIndex + 1) % colors.length;
              currentColor = colors[currentColorIndex].value;
              buildSwatches();
              colorCooldown = 18;
              previousPoint = null;
            } else if (fingers === 4 && toolCooldown === 0) {
              const nextToolIndex = (toolInput.selectedIndex + 1) % toolInput.options.length;
              toolInput.selectedIndex = nextToolIndex;
              toolCooldown = 18;
              previousPoint = null;
              shapeStart = null;
              shapeLast = null;
            } else if (fingers === 5 && gestureEraseInput.checked) {
              shapeStart = null;
              shapeLast = null;
              drawFreehand(point, "Eraser");
            } else {
              previousPoint = null;
            }
          } else {
            previousPoint = null;
            if (shapeStart && shapeLast && ["Line", "Rectangle", "Circle"].includes(toolInput.value)) {
              drawShape(dctx, toolInput.value, shapeStart, shapeLast);
            }
            shapeStart = null;
            shapeLast = null;
          }

          ctx.drawImage(drawing, 0, 0);
          if (shapeStart && shapeLast) drawShape(ctx, toolInput.value, shapeStart, shapeLast, true);
          drawOverlay(results, fingers);
          fingerStatus.textContent = `Fingers: ${fingers}`;
        }

        const hands = new Hands({
          locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });

        hands.setOptions({
          maxNumHands: 1,
          modelComplexity: 1,
          minDetectionConfidence: 0.72,
          minTrackingConfidence: 0.72
        });
        hands.onResults(onResults);

        startBtn.onclick = async () => {
          try {
            camera = new Camera(video, {
              onFrame: async () => {
                await hands.send({ image: video });
              },
              width: 960,
              height: 540
            });
            await camera.start();
            setStatus("Camera running. Show your hand clearly.");
          } catch (error) {
            setStatus(`Camera error: ${error.message}`);
          }
        };

        stopBtn.onclick = () => {
          if (camera) {
            camera.stop();
            camera = null;
          }
          setStatus("Camera stopped.");
        };

        clearBtn.onclick = () => clearCanvas(true);
        undoBtn.onclick = undo;
        saveBtn.onclick = () => {
          const link = document.createElement("a");
          link.download = `hand_gesture_drawing_${new Date().toISOString().replace(/[:.]/g, "-")}.png`;
          link.href = output.toDataURL("image/png");
          link.click();
        };

        brushInput.oninput = () => brushValue.textContent = brushInput.value;
        eraserInput.oninput = () => eraserValue.textContent = eraserInput.value;
        buildSwatches();
      </script>
    </body>
    </html>
    """,
    height=900,
    scrolling=False,
)
