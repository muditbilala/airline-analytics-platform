import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float } from "@react-three/drei";
import type { Mesh, BufferGeometry, Points } from "three";
import * as THREE from "three";

function Stars() {
  const ref = useRef<Points>(null);
  const positions = useMemo(() => {
    const arr = new Float32Array(1500 * 3);
    for (let i = 0; i < 1500; i++) {
      const r = 15 + Math.random() * 25;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  }, []);

  useFrame((_state, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.01;
    }
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial color="#ccd6f6" size={0.06} sizeAttenuation transparent opacity={0.7} />
    </points>
  );
}

function WireframeGlobe() {
  const meshRef = useRef<Mesh>(null);

  useFrame((_state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.15;
      meshRef.current.rotation.x = 0.15;
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[2.5, 32, 32]} />
      <meshBasicMaterial color="#1d3461" wireframe transparent opacity={0.35} />
    </mesh>
  );
}

function GlobeGlow() {
  return (
    <mesh>
      <sphereGeometry args={[2.65, 32, 32]} />
      <meshBasicMaterial color="#e85d3a" transparent opacity={0.04} />
    </mesh>
  );
}

interface ArcProps {
  start: [number, number, number];
  end: [number, number, number];
  color: string;
}

function FlightArc({ start, end, color }: ArcProps) {
  const ref = useRef<Mesh<BufferGeometry>>(null);

  const curve = useMemo(() => {
    const s = new THREE.Vector3(...start);
    const e = new THREE.Vector3(...end);
    const mid = s.clone().add(e).multiplyScalar(0.5);
    mid.normalize().multiplyScalar(4.2);
    return new THREE.QuadraticBezierCurve3(s, mid, e);
  }, [start, end]);

  const geometry = useMemo(() => {
    const points = curve.getPoints(40);
    return new THREE.BufferGeometry().setFromPoints(points);
  }, [curve]);

  useFrame((_state, delta) => {
    if (ref.current) {
      ref.current.rotation.y += delta * 0.15;
    }
  });

  return (
    <line ref={ref as React.RefObject<never>} geometry={geometry}>
      <lineBasicMaterial color={color} transparent opacity={0.5} linewidth={1} />
    </line>
  );
}

const FLIGHT_ARCS: ArcProps[] = [
  { start: [1.8, 1.2, 1.2], end: [-1.5, 0.8, 1.8], color: "#e85d3a" },
  { start: [2.0, 0.5, -1.2], end: [-0.5, 1.8, 1.5], color: "#64ffda" },
  { start: [-1.0, 1.5, 1.8], end: [1.2, -0.8, 2.0], color: "#f07856" },
  { start: [0.5, 2.2, 1.0], end: [-2.0, -0.5, 1.2], color: "#ccd6f6" },
  { start: [1.5, -1.0, 1.8], end: [-1.8, 1.5, -0.5], color: "#e85d3a" },
  { start: [-2.2, 0.3, 1.0], end: [2.0, 1.0, -0.8], color: "#64ffda" },
];

export default function Globe() {
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 45 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.3} />
        <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
          <WireframeGlobe />
          <GlobeGlow />
        </Float>
        {FLIGHT_ARCS.map((arc, i) => (
          <FlightArc key={i} {...arc} />
        ))}
        <Stars />
      </Canvas>
    </div>
  );
}
