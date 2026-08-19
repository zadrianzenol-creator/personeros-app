import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// --- Scene Setup ---
const canvas = document.getElementById('bg');
const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 0, 14);

const renderer = new THREE.WebGLRenderer({
    canvas,
    alpha: true,
    antialias: true,
    powerPreference: "high-performance"
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;

// --- Post-processing ---
const composer = new EffectComposer(renderer);
const renderPass = new RenderPass(scene, camera);
composer.addPass(renderPass);

const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    0.4, 0.2, 0.1
);
composer.addPass(bloomPass);

// --- Lights ---
const ambientLight = new THREE.AmbientLight(0x404060, 0.5);
scene.add(ambientLight);

const pointLight1 = new THREE.PointLight(0x6c5ce7, 20, 30);
pointLight1.position.set(5, 5, 5);
scene.add(pointLight1);

const pointLight2 = new THREE.PointLight(0xfd79a8, 20, 30);
pointLight2.position.set(-5, -3, 5);
scene.add(pointLight2);

const pointLight3 = new THREE.PointLight(0x00cec9, 15, 30);
pointLight3.position.set(0, 6, -5);
scene.add(pointLight3);

// --- Main Torus Knot ---
const knotGeo = new THREE.TorusKnotGeometry(1.8, 0.6, 200, 32);
const knotMat = new THREE.MeshPhysicalMaterial({
    color: 0x6c5ce7,
    metalness: 0.3,
    roughness: 0.2,
    transparent: true,
    opacity: 0.95,
    emissive: 0x6c5ce7,
    emissiveIntensity: 0.08,
    clearcoat: 0.8,
    clearcoatRoughness: 0.3,
    envMapIntensity: 1.5,
});
const torusKnot = new THREE.Mesh(knotGeo, knotMat);
torusKnot.position.y = -0.5;
scene.add(torusKnot);

// --- Inner glow ring ---
const ringGeo = new THREE.TorusGeometry(2.2, 0.03, 32, 64);
const ringMat = new THREE.MeshBasicMaterial({
    color: 0xa29bfe,
    transparent: true,
    opacity: 0.3,
});
const ring = new THREE.Mesh(ringGeo, ringMat);
ring.position.y = -0.5;
scene.add(ring);

// --- Floating geometric shapes ---
const shapes = [];
const shapeColors = [0x6c5ce7, 0xfd79a8, 0x00cec9, 0xfdcb6e, 0xff6b6b];
const shapeGeos = [
    new THREE.IcosahedronGeometry(0.5, 0),
    new THREE.OctahedronGeometry(0.4, 0),
    new THREE.TetrahedronGeometry(0.45, 0),
    new THREE.DodecahedronGeometry(0.35, 0),
];

for (let i = 0; i < 20; i++) {
    const geo = shapeGeos[Math.floor(Math.random() * shapeGeos.length)];
    const mat = new THREE.MeshPhysicalMaterial({
        color: shapeColors[Math.floor(Math.random() * shapeColors.length)],
        metalness: 0.4,
        roughness: 0.3,
        transparent: true,
        opacity: 0.3 + Math.random() * 0.4,
        emissive: shapeColors[Math.floor(Math.random() * shapeColors.length)],
        emissiveIntensity: 0.05,
    });
    const mesh = new THREE.Mesh(geo, mat);

    const radius = 4 + Math.random() * 5;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.random() * Math.PI * 2;

    mesh.position.set(
        Math.sin(theta) * Math.cos(phi) * radius,
        Math.sin(theta) * Math.sin(phi) * radius * 0.6,
        Math.cos(theta) * radius * 0.5
    );

    mesh.userData = {
        speed: 0.2 + Math.random() * 0.3,
        rotSpeed: 0.005 + Math.random() * 0.015,
        theta,
        phi,
        radius,
        offsetY: (Math.random() - 0.5) * 4,
    };

    scene.add(mesh);
    shapes.push(mesh);
}

// --- Particle System ---
const particleCount = 3000;
const positions = new Float32Array(particleCount * 3);
const colors = new Float32Array(particleCount * 3);
const sizes = new Float32Array(particleCount);

const colorPalette = [
    new THREE.Color(0x6c5ce7),
    new THREE.Color(0xa29bfe),
    new THREE.Color(0xfd79a8),
    new THREE.Color(0x00cec9),
];

for (let i = 0; i < particleCount; i++) {
    const radius = 15 + Math.random() * 20;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);

    positions[i * 3] = Math.sin(phi) * Math.cos(theta) * radius;
    positions[i * 3 + 1] = Math.sin(phi) * Math.sin(theta) * radius * 0.4;
    positions[i * 3 + 2] = Math.cos(phi) * radius * 0.6;

    const col = colorPalette[Math.floor(Math.random() * colorPalette.length)];
    colors[i * 3] = col.r;
    colors[i * 3 + 1] = col.g;
    colors[i * 3 + 2] = col.b;

    sizes[i] = 0.5 + Math.random() * 2;
}

const particleGeo = new THREE.BufferGeometry();
particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
particleGeo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

const particleMat = new THREE.PointsMaterial({
    size: 0.06,
    vertexColors: true,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    sizeAttenuation: true,
});

const particles = new THREE.Points(particleGeo, particleMat);
scene.add(particles);

// --- Mouse Tracking ---
const mouse = { x: 0, y: 0 };
let targetRotX = 0;
let targetRotY = 0;

document.addEventListener('mousemove', (e) => {
    mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;

    targetRotX = mouse.y * 0.3;
    targetRotY = mouse.x * 0.3;
});

// Touch support
document.addEventListener('touchmove', (e) => {
    if (e.touches.length > 0) {
        mouse.x = (e.touches[0].clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.touches[0].clientY / window.innerHeight) * 2 + 1;
        targetRotX = mouse.y * 0.3;
        targetRotY = mouse.x * 0.3;
    }
}, { passive: true });

// --- Resize ---
window.addEventListener('resize', () => {
    const w = window.innerWidth;
    const h = window.innerHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
    composer.setSize(w, h);
});

// --- Animation Loop ---
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    const time = clock.getElapsedTime();

    // Smooth camera follow mouse
    torusKnot.rotation.x += (targetRotX - torusKnot.rotation.x) * 0.03;
    torusKnot.rotation.y += (targetRotY - torusKnot.rotation.y) * 0.03;
    torusKnot.rotation.z += 0.003;

    // Ring rotation
    ring.rotation.x = torusKnot.rotation.x;
    ring.rotation.y = torusKnot.rotation.y;
    ring.rotation.z = torusKnot.rotation.z;

    // Pulsing ring
    ring.scale.setScalar(1 + Math.sin(time * 0.5) * 0.02);

    // Floating shapes orbit
    shapes.forEach((mesh, i) => {
        const data = mesh.userData;
        data.theta += data.speed * 0.005;
        data.phi += data.speed * 0.003;

        const radius = data.radius;
        mesh.position.x = Math.sin(data.theta) * Math.cos(data.phi) * radius;
        mesh.position.y = Math.sin(data.theta) * Math.sin(data.phi) * radius * 0.6 + Math.sin(time * 0.3 + i) * 0.3;
        mesh.position.z = Math.cos(data.theta) * radius * 0.5;

        mesh.rotation.x += data.rotSpeed;
        mesh.rotation.y += data.rotSpeed * 0.7;
        mesh.rotation.z += data.rotSpeed * 0.3;
    });

    // Rotate particles slowly
    particles.rotation.y += 0.0003;
    particles.rotation.x += 0.0001;

    // Move lights
    pointLight1.position.x = Math.sin(time * 0.3) * 6;
    pointLight1.position.z = Math.cos(time * 0.3) * 6;
    pointLight2.position.x = Math.sin(time * 0.2 + 2) * 5;
    pointLight2.position.z = Math.cos(time * 0.2 + 2) * 5;
    pointLight3.position.x = Math.sin(time * 0.15 + 4) * 7;
    pointLight3.position.z = Math.cos(time * 0.15 + 4) * 7;

    // Color shift on torus knot
    const hue = (Math.sin(time * 0.05) * 0.5 + 0.5) * 0.2 + 0.65;
    const color = new THREE.Color().setHSL(hue, 0.8, 0.6);
    torusKnot.material.color.set(color);
    torusKnot.material.emissive.set(color);
    ring.material.color.setHSL(hue, 0.7, 0.7);

    // Auto-rotate when no mouse interaction
    if (Math.abs(mouse.x) < 0.02 && Math.abs(mouse.y) < 0.02) {
        torusKnot.rotation.y += 0.002;
        ring.rotation.y += 0.002;
    }

    composer.render();
}

animate();

// --- Scroll-based animations for UI elements ---
function animateCountUp3d(el) {
    const target = parseFloat(el.getAttribute('data-target'));
    const isDecimal = target % 1 !== 0;
    const duration = 2000;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = eased * target;

        if (isDecimal) {
            el.textContent = current.toFixed(1);
        } else {
            el.textContent = Math.floor(current).toLocaleString();
        }

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = isDecimal ? target.toFixed(1) : target.toLocaleString();
        }
    }
    requestAnimationFrame(update);
}

const counters = document.querySelectorAll('.count-up-3d');
let countersCounted = false;

function checkCounters() {
    if (countersCounted) return;
    const section = document.querySelector('.metrics-section');
    if (!section) return;
    const rect = section.getBoundingClientRect();
    if (rect.top < window.innerHeight - 100) {
        countersCounted = true;
        counters.forEach(animateCountUp3d);
    }
}

setTimeout(checkCounters, 500);
window.addEventListener('scroll', checkCounters);

// --- Testimonials rotation ---
const testimonials = [
    {
        text: '"NEXUS 3D transformó completamente nuestra presencia digital. La experiencia 3D en nuestra web aumentó el engagement un 340% y las conversiones un 180%. Es el futuro del diseño web."',
        name: 'María González',
        role: 'CEO — TechVision Corp',
        initial: 'M'
    },
    {
        text: '"Trabajar con NEXUS 3D fue una experiencia revolucionaria. Su enfoque en la experiencia de usuario y la calidad visual es simplemente incomparable. Recomendados al 1000%."',
        name: 'Carlos Mendoza',
        role: 'Director Creativo — PixelStudio',
        initial: 'C'
    },
    {
        text: '"La implementación de realidad aumentada que hicieron para nuestro producto aumentó las ventas un 250%. El equipo de NEXUS 3D entiende de tecnología y de negocio."',
        name: 'Ana Lucía Pérez',
        role: 'CMO — InnovaTech',
        initial: 'A'
    }
];

let testimonialIndex = 0;
const textEl = document.getElementById('testimonialText');
const nameEl = document.getElementById('testimonialName');
const roleEl = document.getElementById('testimonialRole');
const initialEl = document.querySelector('.testimonial-avatar-3d');

if (textEl) {
    setInterval(() => {
        testimonialIndex = (testimonialIndex + 1) % testimonials.length;
        const t = testimonials[testimonialIndex];

        // Fade out
        textEl.style.opacity = '0';
        nameEl.style.opacity = '0';
        roleEl.style.opacity = '0';

        setTimeout(() => {
            textEl.textContent = t.text;
            nameEl.textContent = t.name;
            roleEl.textContent = t.role;
            if (initialEl) initialEl.textContent = t.initial;

            textEl.style.opacity = '1';
            nameEl.style.opacity = '1';
            roleEl.style.opacity = '1';
        }, 400);
    }, 6000);
}

// Style for testimonial transitions
if (textEl) {
    textEl.style.transition = 'opacity 0.4s ease';
    nameEl.style.transition = 'opacity 0.4s ease';
    roleEl.style.transition = 'opacity 0.4s ease';
}

// --- Mobile Menu ---
const hamburger = document.getElementById('glassHamburger');
const mobileMenu = document.getElementById('mobileMenu3d');
const mobileClose = document.getElementById('mobileMenuClose3d');
const overlay = document.getElementById('mobileOverlay3d');

function openMobile() {
    mobileMenu.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeMobile() {
    mobileMenu.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
}

if (hamburger) hamburger.addEventListener('click', openMobile);
if (mobileClose) mobileClose.addEventListener('click', closeMobile);
if (overlay) overlay.addEventListener('click', closeMobile);

const mobileLinks = mobileMenu ? mobileMenu.querySelectorAll('a') : [];
mobileLinks.forEach(link => link.addEventListener('click', closeMobile));

// --- Navbar scroll ---
const glassNav = document.getElementById('glassNav');
window.addEventListener('scroll', () => {
    if (window.scrollY > 80) {
        glassNav.classList.add('scrolled');
    } else {
        glassNav.classList.remove('scrolled');
    }
});

// --- Active nav link ---
const navLinkEls = document.querySelectorAll('.glass-nav-links a');
const sections = document.querySelectorAll('section[id]');

window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
        const top = section.offsetTop - 150;
        if (window.scrollY >= top) {
            current = section.getAttribute('id');
        }
    });
    navLinkEls.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + current) {
            link.classList.add('active');
        }
    });
});

// --- Smooth scroll ---
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
        const href = anchor.getAttribute('href');
        if (href === '#') return;
        const target = document.querySelector(href);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});
