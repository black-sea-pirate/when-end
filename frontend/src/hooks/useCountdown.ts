import { useState, useEffect } from "react";

interface CountdownResult {
  years: number;
  months: number;
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  isOverdue: boolean;
  formatted: string;
}

export function useCountdown(
  effectiveDueAt: string,
  serverNow: string
): CountdownResult {
  const [countdown, setCountdown] = useState<CountdownResult>(() =>
    calculateCountdown(effectiveDueAt, serverNow)
  );

  useEffect(() => {
    // Calculate initial offset between server time and client time
    const serverTime = new Date(serverNow).getTime();
    const clientTime = Date.now();
    const offset = serverTime - clientTime;

    const interval = setInterval(() => {
      const adjustedNow = new Date(Date.now() + offset).toISOString();
      setCountdown(calculateCountdown(effectiveDueAt, adjustedNow));
    }, 1000);

    return () => clearInterval(interval);
  }, [effectiveDueAt, serverNow]);

  return countdown;
}

function calculateCountdown(
  effectiveDueAt: string,
  currentTime: string
): CountdownResult {
  const target = new Date(effectiveDueAt).getTime();
  const now = new Date(currentTime).getTime();
  const diff = target - now;

  if (diff < 0) {
    return {
      years: 0,
      months: 0,
      days: 0,
      hours: 0,
      minutes: 0,
      seconds: 0,
      isOverdue: true,
      formatted: "Overdue",
    };
  }

  // Calculate time components
  const seconds = Math.floor((diff / 1000) % 60);
  const minutes = Math.floor((diff / (1000 * 60)) % 60);
  const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
  const totalDays = Math.floor(diff / (1000 * 60 * 60 * 24));

  // Approximate months and years
  const years = Math.floor(totalDays / 365);
  const remainingDaysAfterYears = totalDays % 365;
  const months = Math.floor(remainingDaysAfterYears / 30);
  const days = remainingDaysAfterYears % 30;

  // Format string
  let formatted = "";

  if (diff < 60000) {
    // Less than 1 minute
    formatted = "< 1 min";
  } else {
    const parts: string[] = [];
    if (years > 0) parts.push(`${years}y`);
    if (months > 0) parts.push(`${months}m`);
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}min`);

    formatted = parts.join(" ");
  }

  return {
    years,
    months,
    days,
    hours,
    minutes,
    seconds,
    isOverdue: false,
    formatted,
  };
}
