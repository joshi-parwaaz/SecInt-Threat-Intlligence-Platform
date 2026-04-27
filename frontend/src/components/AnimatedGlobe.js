import React from 'react';
import { motion } from 'framer-motion';
import { World } from './ui/Globe';

const SecIntGlobe = () => {
  const globeConfig = {
    pointSize: 6,
    globeColor: "#0a0a0a",
    showAtmosphere: true,
    atmosphereColor: "#eab308",
    atmosphereAltitude: 0.2,
    emissive: "#1a1a1a",
    emissiveIntensity: 0.15,
    shininess: 0.3,
    polygonColor: "rgba(234,179,8,0.3)",
    ambientLight: "#606060",
    directionalLeftLight: "#ffffff",
    directionalTopLight: "#ffffff",
    pointLight: "#eab308",
    arcTime: 1500,
    arcLength: 0.9,
    rings: 2,
    maxRings: 4,
    initialPosition: { lat: 40.7128, lng: -74.006 },
    autoRotate: true,
    autoRotateSpeed: 0.8,
    showGraticules: true,
    graticulesColor: "#eab308",
    graticulesOpacity: 0.4,
  };

  const colors = ["#eab308", "#fbbf24", "#f59e0b", "#facc15"];

  // Threat intelligence network connections from global sources
  const threatConnections = [
    // Tier 1 - Major hubs
    {
      order: 1,
      startLat: 40.7128,
      startLng: -74.006, // New York
      endLat: 51.5074,
      endLng: -0.1278, // London
      arcAlt: 0.3,
      color: colors[0],
    },
    {
      order: 1,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: 37.7749,
      endLng: -122.4194, // San Francisco
      arcAlt: 0.4,
      color: colors[1],
    },
    {
      order: 1,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: 35.6762,
      endLng: 139.6503, // Tokyo
      arcAlt: 0.35,
      color: colors[2],
    },
    {
      order: 1,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: 28.6139,
      endLng: 77.209, // Delhi
      arcAlt: 0.4,
      color: colors[3],
    },
    
    // Tier 2 - Regional connections
    {
      order: 2,
      startLat: 51.5074,
      startLng: -0.1278, // London
      endLat: 52.52,
      endLng: 13.405, // Berlin
      arcAlt: 0.2,
      color: colors[0],
    },
    {
      order: 2,
      startLat: 51.5074,
      startLng: -0.1278,
      endLat: 48.8566,
      endLng: 2.3522, // Paris
      arcAlt: 0.15,
      color: colors[1],
    },
    {
      order: 2,
      startLat: 51.5074,
      startLng: -0.1278,
      endLat: 55.7558,
      endLng: 37.6176, // Moscow
      arcAlt: 0.3,
      color: colors[2],
    },
    {
      order: 2,
      startLat: 37.7749,
      startLng: -122.4194, // SF
      endLat: 34.0522,
      endLng: -118.2437, // LA
      arcAlt: 0.2,
      color: colors[3],
    },
    {
      order: 2,
      startLat: 37.7749,
      startLng: -122.4194,
      endLat: 47.6062,
      endLng: -122.3321, // Seattle
      arcAlt: 0.25,
      color: colors[0],
    },
    
    // Tier 3 - Asia Pacific
    {
      order: 3,
      startLat: 35.6762,
      startLng: 139.6503, // Tokyo
      endLat: 1.3521,
      endLng: 103.8198, // Singapore
      arcAlt: 0.35,
      color: colors[1],
    },
    {
      order: 3,
      startLat: 35.6762,
      startLng: 139.6503,
      endLat: 37.5665,
      endLng: 126.978, // Seoul
      arcAlt: 0.2,
      color: colors[2],
    },
    {
      order: 3,
      startLat: 35.6762,
      startLng: 139.6503,
      endLat: 31.2304,
      endLng: 121.4737, // Shanghai
      arcAlt: 0.3,
      color: colors[3],
    },
    {
      order: 3,
      startLat: 28.6139,
      endLng: 77.209, // Delhi
      endLat: 19.076,
      startLng: 72.8777, // Mumbai
      arcAlt: 0.25,
      color: colors[0],
    },
    {
      order: 3,
      startLat: 1.3521,
      startLng: 103.8198, // Singapore
      endLat: 13.7563,
      endLng: 100.5018, // Bangkok
      arcAlt: 0.2,
      color: colors[1],
    },
    
    // Tier 4 - Cross-continental
    {
      order: 4,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: -33.8688,
      endLng: 151.2093, // Sydney
      arcAlt: 0.55,
      color: colors[2],
    },
    {
      order: 4,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: -22.9068,
      endLng: -43.1729, // Rio
      arcAlt: 0.45,
      color: colors[3],
    },
    {
      order: 4,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: -26.2041,
      endLng: 28.0473, // Johannesburg
      arcAlt: 0.5,
      color: colors[0],
    },
    {
      order: 4,
      startLat: 51.5074,
      startLng: -0.1278,
      endLat: 25.2048,
      endLng: 55.2708, // Dubai
      arcAlt: 0.35,
      color: colors[1],
    },
    
    // Tier 5 - Americas
    {
      order: 5,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: 43.6532,
      endLng: -79.3832, // Toronto
      arcAlt: 0.25,
      color: colors[2],
    },
    {
      order: 5,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: 19.4326,
      endLng: -99.1332, // Mexico City
      arcAlt: 0.4,
      color: colors[3],
    },
    {
      order: 5,
      startLat: 40.7128,
      startLng: -74.006,
      endLat: -34.6037,
      endLng: -58.3816, // Buenos Aires
      arcAlt: 0.5,
      color: colors[0],
    },
    {
      order: 5,
      startLat: 37.7749,
      startLng: -122.4194,
      endLat: 49.2827,
      endLng: -123.1207, // Vancouver
      arcAlt: 0.2,
      color: colors[1],
    },
    
    // Tier 6 - Europe
    {
      order: 6,
      startLat: 51.5074,
      startLng: -0.1278,
      endLat: 41.9028,
      endLng: 12.4964, // Rome
      arcAlt: 0.25,
      color: colors[2],
    },
    {
      order: 6,
      startLat: 51.5074,
      startLng: -0.1278,
      endLat: 40.4168,
      endLng: -3.7038, // Madrid
      arcAlt: 0.2,
      color: colors[3],
    },
    {
      order: 6,
      startLat: 51.5074,
      startLng: -0.1278,
      endLat: 59.3293,
      endLng: 18.0686, // Stockholm
      arcAlt: 0.2,
      color: colors[0],
    },
    {
      order: 6,
      startLat: 52.52,
      startLng: 13.405, // Berlin
      endLat: 50.0755,
      endLng: 14.4378, // Prague
      arcAlt: 0.15,
      color: colors[1],
    },
    
    // Tier 7 - Middle East & Africa
    {
      order: 7,
      startLat: 25.2048,
      startLng: 55.2708, // Dubai
      endLat: 24.4539,
      endLng: 54.3773, // Abu Dhabi
      arcAlt: 0.1,
      color: colors[2],
    },
    {
      order: 7,
      startLat: 25.2048,
      startLng: 55.2708,
      endLat: 30.0444,
      endLng: 31.2357, // Cairo
      arcAlt: 0.3,
      color: colors[3],
    },
    {
      order: 7,
      startLat: -26.2041,
      startLng: 28.0473, // Johannesburg
      endLat: -1.2921,
      endLng: 36.8219, // Nairobi
      arcAlt: 0.35,
      color: colors[0],
    },
    {
      order: 7,
      startLat: -26.2041,
      startLng: 28.0473,
      endLat: -33.9249,
      endLng: 18.4241, // Cape Town
      arcAlt: 0.2,
      color: colors[1],
    },
    
    // Tier 8 - Additional APAC
    {
      order: 8,
      startLat: 1.3521,
      startLng: 103.8198, // Singapore
      endLat: 22.3193,
      endLng: 114.1694, // Hong Kong
      arcAlt: 0.3,
      color: colors[2],
    },
    {
      order: 8,
      startLat: 1.3521,
      startLng: 103.8198,
      endLat: 3.139,
      endLng: 101.6869, // Kuala Lumpur
      arcAlt: 0.15,
      color: colors[3],
    },
    {
      order: 8,
      startLat: -33.8688,
      startLng: 151.2093, // Sydney
      endLat: -37.8136,
      endLng: 144.9631, // Melbourne
      arcAlt: 0.2,
      color: colors[0],
    },
    {
      order: 8,
      startLat: -33.8688,
      startLng: 151.2093,
      endLat: -27.4698,
      endLng: 153.0251, // Brisbane
      arcAlt: 0.25,
      color: colors[1],
    },
    
    // Tier 9 - South America
    {
      order: 9,
      startLat: -22.9068,
      startLng: -43.1729, // Rio
      endLat: -23.5505,
      endLng: -46.6333, // São Paulo
      arcAlt: 0.15,
      color: colors[2],
    },
    {
      order: 9,
      startLat: -34.6037,
      startLng: -58.3816, // Buenos Aires
      endLat: -33.4489,
      endLng: -70.6693, // Santiago
      arcAlt: 0.3,
      color: colors[3],
    },
    {
      order: 9,
      startLat: 19.4326,
      startLng: -99.1332, // Mexico City
      endLat: 4.711,
      endLng: -74.0721, // Bogotá
      arcAlt: 0.35,
      color: colors[0],
    },
    
    // Tier 10 - Additional cross-connections
    {
      order: 10,
      startLat: 55.7558,
      startLng: 37.6176, // Moscow
      endLat: 59.9311,
      endLng: 30.3609, // St Petersburg
      arcAlt: 0.15,
      color: colors[1],
    },
    {
      order: 10,
      startLat: 55.7558,
      startLng: 37.6176,
      endLat: 39.9042,
      endLng: 116.4074, // Beijing
      arcAlt: 0.4,
      color: colors[2],
    },
    {
      order: 10,
      startLat: 31.2304,
      startLng: 121.4737, // Shanghai
      endLat: 39.9042,
      endLng: 116.4074, // Beijing
      arcAlt: 0.2,
      color: colors[3],
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full w-full relative">
      {/* Enhanced glow effect */}
      <div className="absolute inset-0 bg-gradient-radial from-yellow-500/20 via-yellow-500/5 to-transparent rounded-full blur-xl" />
      <div className="absolute inset-0 bg-gradient-radial from-yellow-500/10 via-transparent to-transparent rounded-full" />

      <div className="max-w-full mx-auto w-full relative overflow-hidden h-full">
        <motion.div
          initial={{
            opacity: 0,
            y: 20,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 1,
          }}
          className="text-center mb-6 relative z-20"
        >
          <h3 className="text-xl md:text-2xl font-bold text-yellow-500 mb-2 drop-shadow-[0_0_10px_rgba(234,179,8,0.5)]">
            Global Threat Intelligence Network
          </h3>
          <p className="text-sm md:text-base font-normal text-gray-300 max-w-md mx-auto">
            Real-time IOC aggregation from 50+ worldwide sources
          </p>
        </motion.div>

        <div className="absolute w-full bottom-0 inset-x-0 h-32 bg-gradient-to-b pointer-events-none select-none from-transparent via-black/50 to-black z-40" />
        <div className="absolute w-full -bottom-10 h-full z-10 drop-shadow-[0_0_30px_rgba(234,179,8,0.3)]">
          <World data={threatConnections} globeConfig={globeConfig} />
        </div>
      </div>
    </div>
  );
};

export default SecIntGlobe;
