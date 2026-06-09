<script setup lang="ts">
import NezhaCursor from '@/components/NezhaCursor.vue'
import { RouterView } from 'vue-router'
</script>

<template>
  <!-- 路由视图 - 所有页面在这里渲染 -->
  <RouterView />
  <NezhaCursor />
</template>

<style>
/* 全局样式已在 assets/styles/globals.css 中定义 */
</style>
