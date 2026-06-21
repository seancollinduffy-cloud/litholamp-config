"use client";

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

export function ThreeDViewer({ stlUrl, fallbackImage, generationType, params }: any) {
  const [downloadProgress, setDownloadProgress] = React.useState<number | null>(null);
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const meshRef = useRef<THREE.Mesh | null>(null);
  const hardwareMeshRef = useRef<THREE.Mesh | null>(null);
  const groundMeshRef = useRef<THREE.Mesh | null>(null);

  // 1. Initial Setup
  useEffect(() => {
    if (!mountRef.current) return;
    const width = mountRef.current.clientWidth || 1;
    const height = mountRef.current.clientHeight || 500;
    
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(350, 0, 0); 
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.8;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;
    
    let isFloorLamp = params?.hardware === 'TiffanyFloor';
    const textureLoader = new THREE.TextureLoader();
    textureLoader.load(isFloorLamp ? '/textures/cinematic_floor_room.png' : '/textures/cinematic_room.png', (bgTex) => {
        bgTex.mapping = THREE.EquirectangularReflectionMapping;
        bgTex.colorSpace = THREE.SRGBColorSpace;
        scene.background = bgTex;
    });
    renderer.domElement.style.display = 'block';
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    renderer.domElement.style.position = 'absolute';
    renderer.domElement.style.top = '0';
    renderer.domElement.style.left = '0';
    renderer.domElement.style.outline = 'none';
    mountRef.current.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = params?.interactive !== false;
    controls.autoRotateSpeed = 1.0;
    
    // Apply pan/zoom limits
    controls.minDistance = 50;
    controls.maxDistance = 1000;
    controls.maxPolarAngle = Math.PI / 2 + 0.1; // Don't allow camera to go far below the floor
    controls.enablePan = false; // Prevent panning away from the lamp

    scene.add(new THREE.AmbientLight(0x222222)); // Dim ambient light to improve contrast
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.2); // Very dim directional light for twilight mood
    dirLight.position.set(100, 150, 50);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 2048;
    dirLight.shadow.mapSize.height = 2048;
    dirLight.shadow.bias = -0.0005;
    scene.add(dirLight);
    
    const internalLight = new THREE.PointLight(0xffd5a8, params?.brightness || 4.0, 500); // Sepia amber light
    const h = params?.height || 120;
    internalLight.position.set(0, h / 2, 0);
    internalLight.castShadow = true;
    scene.add(internalLight);

    renderer.domElement.addEventListener('click', () => {
      internalLight.visible = !internalLight.visible;
    });

    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const updateCamera = () => {
      if (!mountRef.current || !renderer) return;
      const w = mountRef.current.clientWidth || 1;
      const h_px = mountRef.current.clientHeight || 1;
      renderer.setSize(w, h_px, false); // ONLY update drawing buffer
      camera.aspect = w / h_px;
      camera.updateProjectionMatrix();

      const h_mm = params?.height || 120;
      // Dynamically factor in the height of the hardware base so tall lamps don't clip!
      let totalHeight = h_mm;
      let bottomOffset = 0;
      if (params?.hardware === 'TiffanyFloor') { totalHeight += 450; bottomOffset = -450; }
      else if (params?.hardware === 'TiffanyDesk') { totalHeight += 250; bottomOffset = -250; }
      else { totalHeight += 20; bottomOffset = -20; }

      const centerY = bottomOffset + (totalHeight / 2);
      
      const maxDim = Math.max(params?.diameter || 100, totalHeight);
      const fovRad = camera.fov * (Math.PI / 180);
      let cameraZ = Math.abs(maxDim / 2 / Math.tan(fovRad / 2));
      
      if (camera.aspect < 1) {
          cameraZ = (cameraZ / camera.aspect) * 1.3; 
      } else {
          cameraZ *= 1.25; 
      }
      
      const newTargetY = centerY; 
      
      const offset = new THREE.Vector3().subVectors(camera.position, controls.target);
      if (offset.length() === 0) offset.set(0, 0, 1);
      offset.normalize().multiplyScalar(cameraZ);
      
      controls.target.set(0, newTargetY, 0);
      camera.position.copy(controls.target).add(offset);
      controls.update();
    };

    const handleResize = () => updateCamera();

    const resizeObserver = new ResizeObserver(() => handleResize());
    resizeObserver.observe(mountRef.current);
    
    // Initial frame
    updateCamera();

    return () => {
      cancelAnimationFrame(animId);
      resizeObserver.disconnect();
      controls.dispose();
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [params?.height, params?.diameter, params?.hardware]); // Re-run setup if dimensions or hardware change

  // 2. Mesh Management (Fallback vs STL)
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    if (meshRef.current) {
      scene.remove(meshRef.current);
      if (meshRef.current.geometry) meshRef.current.geometry.dispose();
      meshRef.current = null;
    }
    
    if (hardwareMeshRef.current) {
      scene.remove(hardwareMeshRef.current);
      if (hardwareMeshRef.current.geometry) hardwareMeshRef.current.geometry.dispose();
      hardwareMeshRef.current = null;
    }

    if (groundMeshRef.current) {
      scene.remove(groundMeshRef.current);
      if (groundMeshRef.current.geometry) groundMeshRef.current.geometry.dispose();
      groundMeshRef.current = null;
    }

    let isFloorLamp = params?.hardware === 'TiffanyFloor';
    const textureLoader = new THREE.TextureLoader();
    const groundTex = textureLoader.load(isFloorLamp ? '/textures/hardwood_floor.png' : '/textures/cinematic_desk.png');
    groundTex.wrapS = THREE.RepeatWrapping;
    groundTex.wrapT = THREE.RepeatWrapping;
    groundTex.repeat.set(8, 8);
    groundTex.colorSpace = THREE.SRGBColorSpace;

    const groundGeo = new THREE.PlaneGeometry(2000, 2000);
    const groundMat = new THREE.MeshStandardMaterial({
        map: groundTex,
        roughness: isFloorLamp ? 0.4 : 0.6, // Matte desk
        metalness: 0.0
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -20; // Default, will be updated by base geometry
    ground.receiveShadow = true;
    scene.add(ground);
    groundMeshRef.current = ground;

    let isActive = true;

    // Load hardware placeholder
    const hwLoader = new STLLoader();
    hwLoader.load(`/models/${params?.hardware || 'RoundWoodBase'}.stl`, function (geometry) {
      if (!isActive) return;
      let color = 0x808080;
      let roughness = 0.8;
      let metalness = 0.1;

      if (params?.hardware === 'RoundWoodBase' || params?.hardware === 'SquareWoodBase') {
        color = 0xe6c29e; // light wood
        roughness = 0.4;
      } else if (params?.hardware === 'DarkWoodBase') {
        color = 0x4a3219; // dark wood
        roughness = 0.2; // glossy finish
      } else if (params?.hardware === 'TiffanyDesk' || params?.hardware === 'TiffanyFloor') {
        color = 0xb08d57; // realistic bronze
        roughness = 0.2;
        metalness = 1.0;
      }

      const material = new THREE.MeshStandardMaterial({ color, roughness, metalness });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.rotation.x = -Math.PI / 2;
      mesh.rotation.z = Math.PI; // Rotate 180 degrees so the power cord hole faces the back
      mesh.position.y = 0; // Move base down 
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      scene.add(mesh);
      hardwareMeshRef.current = mesh;

      geometry.computeBoundingBox();
      if (geometry.boundingBox && groundMeshRef.current) {
          groundMeshRef.current.position.y = geometry.boundingBox.min.z - 0.1;
      }
    });

    if (stlUrl) {
      setDownloadProgress(0);
      const loader = new STLLoader();
      loader.load(stlUrl, (geometry) => {
        setDownloadProgress(null);
        if (!isActive) return;
        geometry.computeBoundingBox();
        const centerOffset = new THREE.Vector3();
        if (geometry.boundingBox) {
            geometry.boundingBox.getCenter(centerOffset).multiplyScalar(-1);
            geometry.translate(centerOffset.x, centerOffset.y, 0); // Fix: Do not translate Z so bottom is at Z=0
        }
        
        // --- Fake Preview: Generate UVs for the loaded STL ---
        const pos = geometry.attributes.position;
        const uvs = new Float32Array(pos.count * 2);
        
        const minZ = geometry.boundingBox!.min.z;
        const maxZ = geometry.boundingBox!.max.z;
        const rangeZ = maxZ - minZ || 1;

        for (let i = 0; i < pos.count; i += 3) {
            for (let j = 0; j < 3; j++) {
                const x = pos.getX(i + j);
                const y = pos.getY(i + j);
                const z = pos.getZ(i + j);
                
                let u = Math.atan2(y, x) / (2 * Math.PI);
                u = u < 0 ? u + 1 : u;
                
                if (params?.shape === 'Cylinder' || params?.shape === 'Tiffany') {
                    u = (u + 0.5) % 1.0;
                }
                
                let v = (z - minZ) / rangeZ;

                if (params?.shape === 'Tiffany') {
                    const scale = 1.0 - v * 0.4; 
                    u = 0.5 + (u - 0.5) * scale;
                } else if (params?.shape === 'Square') {
                    u = (u * 4) % 1.0; 
                }
                
                uvs[(i + j) * 2] = u;
                uvs[(i + j) * 2 + 1] = v;
            }
            
            // Fix UV wrap-around seam for this triangle
            let u0 = uvs[i * 2];
            let u1 = uvs[(i + 1) * 2];
            let u2 = uvs[(i + 2) * 2];
            
            if (Math.max(u0, u1, u2) - Math.min(u0, u1, u2) > 0.5) {
                if (u0 < 0.5) uvs[i * 2] += 1.0;
                if (u1 < 0.5) uvs[(i + 1) * 2] += 1.0;
                if (u2 < 0.5) uvs[(i + 2) * 2] += 1.0;
            }
        }
        
        geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
        
        const material = new THREE.MeshPhysicalMaterial({
          color: 0xcccccc, // Darken base plastic so unlit areas look dark (emissive is additive!)
          roughness: 0.5, // slightly rougher plastic
          metalness: 0.0,
          transmission: 0.0, // Remove glass transmission to fix emissive map
          thickness: params?.thickness || 3.0,
          side: THREE.DoubleSide
        });

        // Apply the image as an emissive map for the STL
        if (generationType === 'lithophane' && fallbackImage) {
          const img = new window.Image();
          img.onload = () => {
            if (!isActive) return;
            const canvas = document.createElement('canvas');
            const targetW = 1024;
            
            // Aspect ratio calculation depends on shape!
            let cylAspect = (Math.PI * (params?.diameter || 100)) / (params?.height || 120);
            if (params?.shape === 'Square') {
               cylAspect = (params?.diameter || 90) / (params?.height || 120);
            }
            
            let targetH = Math.round(targetW / cylAspect);
            canvas.width = targetW;
            canvas.height = targetH;
            
            const ctx = canvas.getContext('2d');
            if (!ctx) return;
            
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, targetW, targetH);
            
            if (params?.shape === 'Square') {
                 // Exact 5mm border logic!
                 const faceWidth = params?.diameter || 90;
                 const faceHeight = params?.height || 120;
                 const marginX = targetW * (5 / faceWidth);
                 const marginY = targetH * (5 / faceHeight);
                 ctx.drawImage(img, marginX, marginY, targetW - 2*marginX, targetH - 2*marginY);
            } else {
                 const imgAspect = img.width / img.height;
                 let drawW = targetW;
                 let drawH = targetH;
                 let dx = 0;
                 let dy = 0;
                 
                 if (imgAspect < cylAspect) {
                    drawH = targetH;
                    drawW = targetH * imgAspect;
                    dx = (targetW - drawW) / 2;
                 } else {
                    drawW = targetW;
                    drawH = targetW / imgAspect;
                    dy = (targetH - drawH) / 2;
                 }
                 ctx.drawImage(img, dx, dy, drawW, drawH);
            }
            
            const imageData = ctx.getImageData(0, 0, targetW, targetH);
            const data = imageData.data;
            for (let i = 0; i < data.length; i += 4) {
               const gray = data[i] * 0.299 + data[i+1] * 0.587 + data[i+2] * 0.114;
               data[i] = gray;
               data[i+1] = gray;
               data[i+2] = gray;
            }
            ctx.putImageData(imageData, 0, 0);
            
            const texture = new THREE.CanvasTexture(canvas);
            texture.wrapS = THREE.RepeatWrapping;
            texture.wrapT = THREE.ClampToEdgeWrapping;
            
            material.emissiveMap = texture;
            material.emissive = new THREE.Color(0xffd5a8); // Cinematic sepia/amber glow
            material.emissiveIntensity = params?.brightness || 1.8; // Lower intensity slightly to preserve darks
            material.needsUpdate = true;
          };
          img.src = fallbackImage;
        }

        const mesh = new THREE.Mesh(geometry, material);
        mesh.rotation.x = -Math.PI / 2; // STL orientation fix
        if (params?.hardware === 'SquareWoodBase') {
            mesh.rotation.z = Math.PI / 4; // Align square lampshade corners with the hardware base
        }
        scene.add(mesh);
        meshRef.current = mesh;
      }, (xhr) => {
        if (xhr.lengthComputable && isActive) {
            setDownloadProgress(Math.round((xhr.loaded / xhr.total) * 100));
        }
      });
    } else {
        const texture = new THREE.CanvasTexture(document.createElement('canvas')); // placeholder
        const material = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            roughness: 0.3,
            metalness: 0.1,
            map: texture,
            displacementMap: texture,
            displacementScale: params?.thickness || 3.0,
            side: THREE.DoubleSide
          });
  
      if (generationType === 'lithophane' && fallbackImage) {
        const img = new window.Image();
        img.onload = () => {
          if (!isActive) return;
          const canvas = document.createElement('canvas');
          const cylAspect = (Math.PI * (params?.diameter || 100)) / (params?.height || 120);
          
          let targetW = 1024;
          let targetH = Math.round(1024 / cylAspect);
          canvas.width = targetW;
          canvas.height = targetH;
          
          const ctx = canvas.getContext('2d');
          if (!ctx) return;
          
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, targetW, targetH);
          
          const imgAspect = img.width / img.height;
          let drawW = targetW;
          let drawH = targetH;
          let dx = 0;
          let dy = 0;
          
          if (imgAspect < cylAspect) {
             drawH = targetH;
             drawW = targetH * imgAspect;
             dx = (targetW - drawW) / 2;
          } else {
             drawW = targetW;
             drawH = targetW / imgAspect;
             dy = (targetH - drawH) / 2;
          }
          
          ctx.drawImage(img, dx, dy, drawW, drawH);
          
          const imageData = ctx.getImageData(0, 0, targetW, targetH);
          const data = imageData.data;
          for (let i = 0; i < data.length; i += 4) {
             const gray = data[i] * 0.299 + data[i+1] * 0.587 + data[i+2] * 0.114;
             data[i] = gray;
             data[i+1] = gray;
             data[i+2] = gray;
          }
          ctx.putImageData(imageData, 0, 0);
          
          const texture = new THREE.CanvasTexture(canvas);
          texture.wrapS = THREE.RepeatWrapping;
          texture.wrapT = THREE.ClampToEdgeWrapping;
          
          material.displacementMap = texture;
          material.displacementScale = -(params?.thickness || 3.0) * 0.8;
          material.displacementBias = (params?.thickness || 3.0) * 0.4;
          
          material.emissiveMap = texture;
          material.emissive = new THREE.Color(0x555555); // Neutral white/grey so photo looks accurate
          material.emissiveIntensity = (params?.brightness || 1.0);
          material.needsUpdate = true;
        };
        img.src = fallbackImage;
      } else if (generationType === 'voronoi') {
        material.wireframe = true;
      }
      
      const r = (params?.diameter || 100) / 2;
      const h = params?.height || 120;
      let geometry;
      if (params?.shape === 'Square') {
        geometry = new THREE.CylinderGeometry(r, r, h, 4, 128, true);
        geometry.rotateY(Math.PI / 4);
      } else if (params?.shape === 'Tiffany') {
        geometry = new THREE.CylinderGeometry(r * 0.6, r, h, 256, 128, true);
      } else {
        geometry = new THREE.CylinderGeometry(r, r, h, 256, 128, true);
      }
      geometry.translate(0, h/2, 0); // Put bottom of placeholder at Y=0
          const stlMesh = new THREE.Mesh(geometry, material);
          stlMesh.castShadow = true;
          stlMesh.receiveShadow = true;
          scene.add(stlMesh);
          meshRef.current = stlMesh;
    }

    return () => {
      isActive = false;
    };
  }, [stlUrl, fallbackImage, generationType, params?.diameter, params?.height, params?.thickness, params?.hardware]);

  return (
    <div className="relative w-full h-[500px]" style={{ background: 'transparent' }}>
      {downloadProgress !== null && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50 text-white z-10 flex-col backdrop-blur-sm rounded-xl">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-xl font-bold font-['Outfit']">Downloading 3D Preview: {downloadProgress}%</p>
          <p className="text-sm text-emerald-300 mt-2">Loading high-resolution mesh</p>
        </div>
      )}
      <div ref={mountRef} className="w-full h-full" style={{ outline: 'none' }} />
      {!stlUrl && (
        <div className="absolute top-4 left-4 bg-black/50 text-white text-xs px-3 py-1 rounded-full border border-white/20 pointer-events-none">
          Rough Preview - Click Generate for Final Mesh
        </div>
      )}
    </div>
  );
}
