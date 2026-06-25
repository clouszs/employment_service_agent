import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as monitorApi from '@/api/monitor'
import type { KbHealthLatest, LlmCostDailyRead, RefusalStats } from '@/types/monitor'

export const useMonitorStore = defineStore('monitor', () => {
  const kbHealth = ref<KbHealthLatest | null>(null)
  const llmCostDaily = ref<LlmCostDailyRead | null>(null)
  const refusalStats = ref<RefusalStats | null>(null)

  const loadingHealth = ref(false)
  const loadingCost = ref(false)
  const loadingRefusal = ref(false)

  async function loadKbHealthLatest() {
    loadingHealth.value = true
    try {
      kbHealth.value = await monitorApi.getKbHealthLatest()
    } finally {
      loadingHealth.value = false
    }
  }

  async function loadLlmCostDaily() {
    loadingCost.value = true
    try {
      llmCostDaily.value = await monitorApi.getLlmCostDaily()
    } finally {
      loadingCost.value = false
    }
  }

  async function loadRefusalStats() {
    loadingRefusal.value = true
    try {
      refusalStats.value = await monitorApi.getRefusalStats()
    } finally {
      loadingRefusal.value = false
    }
  }

  async function refreshDashboardCards() {
    await Promise.all([
      loadKbHealthLatest(),
      loadLlmCostDaily(),
      loadRefusalStats(),
    ])
  }

  return {
    kbHealth,
    llmCostDaily,
    refusalStats,
    loadingHealth,
    loadingCost,
    loadingRefusal,
    loadKbHealthLatest,
    loadLlmCostDaily,
    loadRefusalStats,
    refreshDashboardCards,
  }
})
