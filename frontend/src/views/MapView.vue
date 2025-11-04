<script setup lang="ts">
import Map from '../components/Map.vue'
</script>

<template>
  <div class="map-view">
    <Map />
  </div>
</template>

<style scoped>
.map-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
