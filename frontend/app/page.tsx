'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { getApiUrl } from './utils/apiClient';
import CommandCenter from './components/CommandCenter';

export default function Home() {
  const [scheduledVideos, setScheduledVideos] = useState([]);

  useEffect(() => {
    const fetchSchedule = async () => {
      try {
        const res = await axios.get(`${getApiUrl()}/api/v1/scheduler/items`);
        setScheduledVideos(res.data);
      } catch (err) {
        console.error("Failed to fetch schedule", err);
      }
    };
    fetchSchedule();
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold text-white mb-2 font-display uppercase tracking-widest flex items-center gap-3">
        <span className="material-symbols-outlined text-cyan-500">rocket_launch</span>
        Comando Celestial Pro
      </h1>

      <CommandCenter scheduledVideos={scheduledVideos} />
    </div>
  );
}
