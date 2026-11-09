import { create } from "zustand";

interface StreamState {
  connected: boolean;
  lastMessage: string | null;
  setConnected: (v: boolean) => void;
  push: (msg: string) => void;
}

export const useStream = create<StreamState>((set) => ({
  connected: false,
  lastMessage: null,
  setConnected: (connected) => set({ connected }),
  push: (lastMessage) => set({ lastMessage }),
}));
