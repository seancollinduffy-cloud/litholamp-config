from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from typing import List
import subprocess, os, uuid, shutil

app = FastAPI()
RENDER_DIR = os.path.join(os.getcwd(), "customer_renders")
os.makedirs(RENDER_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home():
    return """<html><head><title>Litho Engine | Design Suite</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/loaders/STLLoader.js"></script>
<script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/controls/OrbitControls.js"></script>
</head>
<body style="margin:0; background:#050505; color:white; font-family:sans-serif; display:flex; height:100vh; overflow:hidden;">
    <div style="width:380px; background:#111; padding:20px; border-right:1px solid #333; display:flex; flex-direction:column; gap:20px; overflow-y:auto;">
        <div style="font-size:22px; font-weight:900; color:#28a745; margin-bottom:10px; letter-spacing:1px;">LITHO <span style="color:white; font-weight:100">ENGINE</span></div>
        
        <div style="font-size:10px; color:#666; letter-spacing:1px;">1. GEOMETRY</div>
        <div style="display:flex; overflow-x:auto; gap:10px; padding-bottom:10px;">
            <div class="card" style="min-width:100px; padding:15px 5px; background:#1b2e1e; border:2px solid #28a745; border-radius:8px; cursor:pointer; text-align:center; flex:0 0 auto;" onclick="setS(this,'Cylinder',1)">Cylinder</div>
            <div class="card" style="min-width:100px; padding:15px 5px; background:#1a1a1a; border:2px solid #333; border-radius:8px; cursor:pointer; text-align:center; flex:0 0 auto;" onclick="setS(this,'Square',4)">Square</div>
            <div class="card" style="min-width:100px; padding:15px 5px; background:#1a1a1a; border:2px solid #333; border-radius:8px; cursor:pointer; text-align:center; flex:0 0 auto;" onclick="setS(this,'Hexagon',6)">Hexagon</div>
            <div class="card" style="min-width:100px; padding:15px 5px; background:#1a1a1a; border:2px solid #333; border-radius:8px; cursor:pointer; text-align:center; flex:0 0 auto;" onclick="setS(this,'Octagon',8)">Octagon</div>
        </div>

        <div style="font-size:10px; color:#666; letter-spacing:1px;">2. PATTERN</div>
        <div id="plist" style="display:flex; overflow-x:auto; gap:10px; padding-bottom:10px;"></div>

        <div style="font-size:10px; color:#666; letter-spacing:1px;">3. ASSETS</div>
        <div id="slots" style="background:#000; padding:15px; border-radius:8px; border:1px solid #222;"></div>

        <div style="font-size:10px; color:#666; letter-spacing:1px;">4. MOUNTING</div>
        <div style="display:flex; overflow-x:auto; gap:10px; padding-bottom:10px;">
            <div class="card" style="min-width:100px; padding:15px 5px; background:#1b2e1e; border:2px solid #28a745; border-radius:8px; cursor:pointer; text-align:center; flex:0 0 auto;" onclick="setH(this,'E26')">E26</div>
            <div class="card" style="min-width:100px; padding:15px 5px; background:#1a1a1a; border:2px solid #333; border-radius:8px; cursor:pointer; text-align:center; flex:0 0 auto;" onclick="setH(this,'E12')">E12</div>
            <div class="card" style="min-width:100px; padding:15px 5px; background:#1a1a1a; border:2px solid #333; border-radius:8px; cursor:pointer; text-align:center; flex:0 0 auto;" onclick="setH(this,'Base')">Base</div>
        </div>

        <button style="background:#28a745; color:white; padding:20px; border:none; border-radius:10px; font-weight:bold; cursor:pointer; margin-top:auto;" onclick="go()">PRODUCE STL</button>
    </div>
    <div id="v" style="flex:1; background:#000; position:relative;">
        <div id="status" style="position:absolute; top:20px; left:20px; background:rgba(0,0,0,0.8); padding:10px 20px; border-radius:20px; border:1px solid #28a745; font-size:12px; z-index:100;">Ready</div>
    </div>
<script>
    let conf={s:'Cylinder',h:'E26',sides:1,imgs:1};
    let scene, cam, r, ctrl, hwMesh;

    function initThree() {
        scene=new THREE.Scene(); cam=new THREE.PerspectiveCamera(75,(window.innerWidth-380)/window.innerHeight,0.1,1000);
        r=new THREE.WebGLRenderer({antialias:true}); r.setSize(window.innerWidth-380,window.innerHeight);
        document.getElementById('v').appendChild(r.domElement);
        scene.add(new THREE.AmbientLight(0x404040), new THREE.DirectionalLight(0xffffff,1.5));
        ctrl=new THREE.OrbitControls(cam,r.domElement); cam.position.set(0,100,250);
        updateHardwareVisual();
        animate();
    }

    function updateHardwareVisual() {
        if(hwMesh) scene.remove(hwMesh);
        const geo = conf.h === 'Base' ? new THREE.CylinderGeometry(40, 45, 20, 32) : new THREE.SphereGeometry(15, 32, 32);
        const mat = new THREE.MeshPhongMaterial({color:0x333333, wireframe:true});
        hwMesh = new THREE.Mesh(geo, mat);
        hwMesh.position.y = conf.h === 'Base' ? 10 : 100;
        scene.add(hwMesh);
    }

    function setS(el,n,s){
        el.parentElement.querySelectorAll('.card').forEach(c=>{c.style.background='#1a1a1a';c.style.borderColor='#333';});
        el.style.background='#1b2e1e';el.style.borderColor='#28a745';
        conf.s=n; conf.sides=s; updateP();
    }
    function updateP(){
        const l=document.getElementById('plist'); l.innerHTML='';
        [1,2,3,4,6,8].forEach(v=>{
            if(conf.sides%v==0){
                const bg = v==1?'#1b2e1e':'#1a1a1a'; const bc = v==1?'#28a745':'#333';
                l.innerHTML+=`<div class="card" style="min-width:100px; padding:15px 5px; background:${bg}; border:2px solid ${bc}; border-radius:8px; cursor:pointer; text-align:center; flex:0 0 auto;" onclick="setI(this,${v})">${v} Img</div>`;
            }
        });
        setI(l.firstChild,1);
    }
    function setI(el,v){
        if(!el)return;
        el.parentElement.querySelectorAll('.card').forEach(c=>{c.style.background='#1a1a1a';c.style.borderColor='#333';});
        el.style.background='#1b2e1e';el.style.borderColor='#28a745';
        conf.imgs=v; const s=document.getElementById('slots'); s.innerHTML='';
        for(let i=0; i<v; i++) s.innerHTML+=`<input type="file" id="f${i}" style="display:block;margin-bottom:8px;font-size:10px;color:#888;">`;
    }
    function setH(el,h){
        el.parentElement.querySelectorAll('.card').forEach(c=>{c.style.background='#1a1a1a';c.style.borderColor='#333';});
        el.style.background='#1b2e1e';el.style.borderColor='#28a745';
        conf.h=h; updateHardwareVisual();
    }
    async function go(){
        const st=document.getElementById('status'); st.innerText="Compiling Mesh...";
        const d=new FormData(); d.append('hardware',conf.h); d.append('shape',conf.s); d.append('sides',conf.sides);
        for(let i=0; i<conf.imgs; i++){ const f=document.getElementById('f'+i).files[0]; if(f) d.append('files',f); }
        const res=await fetch('/generate',{method:'POST',body:d}); const data=await res.json();
        new THREE.STLLoader().load('/download/'+data.job_id,(g)=>{
            if(window.m)scene.remove(window.m); window.m=new THREE.Mesh(g,new THREE.MeshPhongMaterial({color:0xffffff, transparent:true, opacity:0.95}));
            window.m.rotation.x=-Math.PI/2; scene.add(window.m); st.innerHTML="Complete";
        });
    }
    function animate(){requestAnimationFrame(animate);ctrl.update();r.render(scene,cam)}
    window.onload = initThree;
</script></body></html>"""

@app.post("/generate")
async def handle_generate(files: List[UploadFile]=File(...), hardware: str=Form(...), shape: str=Form(...), sides: int=Form(...)):
    jid=str(uuid.uuid4()); p=os.path.join(RENDER_DIR, jid); os.makedirs(p, exist_ok=True)
    for i,f in enumerate(files):
        with open(os.path.join(p,f"input_{i}.png"),"wb") as b: b.write(await f.read())
    subprocess.run(["python3", "cylinder_render.py", p, hardware, shape, str(sides), str(len(files))], check=True)
    return {"job_id":jid}

@app.get("/download/{jid}")
async def dl(jid: str): return FileResponse(os.path.join(RENDER_DIR, jid, "final.stl"))
