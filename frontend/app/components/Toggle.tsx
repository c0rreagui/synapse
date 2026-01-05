"use client";

// import { useState } from "react";

interface ToggleProps {
    checked: boolean;
    onChange: (checked: boolean) => void;
    disabled?: boolean;
    label?: string;
    id?: string;
}

export default function Toggle({ checked, onChange, disabled = false, label, id }: ToggleProps) {
    return (
        <label className="flex items-center cursor-pointer relative" htmlFor={id}>
            <input
                type="checkbox"
                id={id}
                checked={checked}
                onChange={(e) => onChange(e.target.checked)}
                disabled={disabled}
                className="sr-only peer"
                aria-label={label || "Toggle switch"}
            />
            <div
                className={`w-11 h-6 rounded-full border transition-colors duration-300 ${disabled
                    ? "bg-gray-800 border-gray-700"
                    : checked
                        ? "bg-primary border-primary"
                        : "bg-gray-700 border-gray-600"
                    }`}
            ></div>
            <div
                className={`dot absolute left-1 top-1 w-4 h-4 rounded-full transition-transform duration-300 ${checked ? "translate-x-5 bg-white" : "translate-x-0"
                    } ${disabled ? "bg-gray-400" : "bg-white"}`}
            ></div>
        </label>
    );
}
