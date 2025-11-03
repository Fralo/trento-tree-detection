<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { LMap, LTileLayer, LWmsTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

interface Tree {
  id: number
  latitude: number
  longitude: number
}

const trees = ref<Tree[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

// Florence coordinates
const center = ref<[number, number]>([43.7696, 11.2558])
const zoom = ref(13)

const fetchTrees = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await fetch('http://localhost:8000/trees')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    trees.value = data
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to fetch trees'
    console.error('Error fetching trees:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTrees()
})
</script>

<template>
  <div class="map-container">
    <div v-if="loading" class="loading">Loading trees...</div>
    <div v-if="error" class="error">Error: {{ error }}</div>
    <l-map v-model:zoom="zoom" v-model:center="center" :use-global-leaflet="false" class="map">
      <l-wms-tile-layer
        url="https://www502.regione.toscana.it/ows_ofc/com.rt.wms.RTmap/wms"
        :layers="'rt_ofc.5k23.32bit'"
        :styles="''"
        :format="'image/png'"
        :transparent="true"
        :version="'1.3.0'"
        attribution="&copy; <a href='https://www.regione.toscana.it/'>Regione Toscana</a>"
        layer-type="base"
        name="Regione Toscana Ortofoto"
        :options="{
          map: 'owsofc_rt',
          exceptions: 'INIMAGE',
        }"
      />
      <l-marker v-for="tree in trees" :key="tree.id" :lat-lng="[tree.latitude, tree.longitude]">
        <l-popup>
          <div class="tree-popup">
            <strong>Tree ID:</strong> {{ tree.id }}<br />
            <span v-if="tree.species"><strong>Species:</strong> {{ tree.species }}<br /></span>
            <strong>Location:</strong> {{ tree.latitude.toFixed(6) }},
            {{ tree.longitude.toFixed(6) }}
          </div>
        </l-popup>
      </l-marker>
    </l-map>
  </div>
</template>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.map {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

.loading,
.error {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.error {
  background: #fee;
  color: #c33;
}

.tree-popup {
  font-size: 14px;
  line-height: 1.5;
}
</style>
