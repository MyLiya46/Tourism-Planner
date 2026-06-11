<script setup lang="ts">
import { ref } from "vue";

import type { Itinerary } from "./types";
import History from "./views/History.vue";
import Home from "./views/Home.vue";
import Result from "./views/Result.vue";

const currentView = ref<"home" | "result" | "history">("home");
const latestItinerary = ref<Itinerary | null>(null);

function handleGenerated(itinerary: Itinerary) {
  latestItinerary.value = itinerary;
  currentView.value = "result";
}

function openTrip(itinerary: Itinerary) {
  latestItinerary.value = itinerary;
  currentView.value = "result";
}

function updateCurrentItinerary(itinerary: Itinerary) {
  latestItinerary.value = itinerary;
  currentView.value = "result";
}
</script>

<template>
  <div class="app-shell">
    <div class="app-shell__glow app-shell__glow--left"></div>
    <div class="app-shell__glow app-shell__glow--right"></div>

    <header class="hero">
      <div class="hero__badge">Trip Planner Demo</div>
      <h1 class="hero__title">智能旅行助手</h1>

      <div class="hero__tabs">
        <button
          :class="['hero__tab', { 'hero__tab--active': currentView === 'home' }]"
          @click="currentView = 'home'"
        >
          规划页
        </button>
        <button
          :class="[
            'hero__tab',
            { 'hero__tab--active': currentView === 'result' },
            { 'hero__tab--disabled': !latestItinerary }
          ]"
          :disabled="!latestItinerary"
          @click="currentView = 'result'"
        >
          结果页
        </button>
        <button
          :class="['hero__tab', { 'hero__tab--active': currentView === 'history' }]"
          @click="currentView = 'history'"
        >
          历史列表
        </button>
      </div>
    </header>

    <main class="page-content">
      <Home
        v-if="currentView === 'home'"
        @generated="handleGenerated"
      />
      <Result
        v-else-if="currentView === 'result'"
        :itinerary="latestItinerary"
        @back-home="currentView = 'home'"
        @view-history="currentView = 'history'"
        @updated="updateCurrentItinerary"
      />
      <History
        v-else
        :active="currentView === 'history'"
        @open-trip="openTrip"
      />
    </main>
  </div>
</template>

<style scoped>
:global(body) {
  margin: 0;
  min-width: 320px;
  font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(175, 198, 255, 0.55), transparent 28%),
    radial-gradient(circle at right 18%, rgba(181, 150, 255, 0.3), transparent 20%),
    linear-gradient(180deg, #eef4ff 0%, #edf2f9 100%);
  color: #1f2937;
}

:global(*) {
  box-sizing: border-box;
}

.app-shell {
  position: relative;
  min-height: 100vh;
  padding: 40px 24px 64px;
  overflow: hidden;
}

.app-shell__glow {
  position: absolute;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  filter: blur(24px);
  opacity: 0.5;
  pointer-events: none;
}

.app-shell__glow--left {
  top: -110px;
  left: -90px;
  background: rgba(113, 132, 255, 0.45);
}

.app-shell__glow--right {
  right: -80px;
  bottom: 120px;
  background: rgba(155, 116, 255, 0.25);
}

.hero {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto 28px;
  text-align: center;
}

.hero__badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: #5c6ac4;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
  box-shadow: 0 12px 30px rgba(98, 116, 164, 0.1);
}

.hero__title {
  margin: 18px 0 0;
  color: #ffffff;
  font-size: 48px;
  line-height: 1.1;
}

.hero::before {
  content: "";
  position: absolute;
  inset: -24px 0 auto;
  height: 220px;
  z-index: -1;
  border-radius: 36px;
  background: linear-gradient(135deg, #6d82de 0%, #6f72d9 52%, #8c67cf 100%);
  box-shadow: 0 32px 80px rgba(95, 110, 172, 0.3);
}

.hero__tabs {
  display: inline-flex;
  gap: 10px;
  margin-top: 24px;
  padding: 8px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(10px);
}

.hero__tab {
  border: none;
  border-radius: 12px;
  padding: 10px 18px;
  background: transparent;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.hero__tab--active {
  background: rgba(255, 255, 255, 0.92);
  color: #5f60c8;
}

.hero__tab--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-content {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .app-shell {
    padding: 24px 16px 40px;
  }

  .hero__title {
    font-size: 34px;
  }

  .hero::before {
    inset: -20px 0 auto;
    height: 230px;
  }
}
</style>
