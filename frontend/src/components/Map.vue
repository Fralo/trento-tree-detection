<script setup lang="ts">
import { ref, watch, shallowRef } from 'vue'
import { LMap, LWmsTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L, { type LatLngBounds, type Map as LeafletMap } from 'leaflet'
import { api } from '@/services/api'
import type { Tree } from '@/types/tree'

const trees = ref<Tree[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const bounds = ref<LatLngBounds | null>(null)
const mapRef = shallowRef<LeafletMap | null>(null)

// Florence coordinates
const center = ref<[number, number]>([43.7696, 11.2558])
const zoom = ref(13)

let fetchTimeout: ReturnType<typeof setTimeout> | null = null
const FETCH_DEBOUNCE_MS = 500

const fetchTreesInBounds = async (mapBounds: LatLngBounds, currentZoom: number) => {
    // Progressive zoom levels - require higher zoom for more trees
    const minZoomForTrees = 17

    if (currentZoom < minZoomForTrees) {
        // Clear trees when zoomed out
        trees.value = []
        return
    }

    // Don't fetch if map isn't ready
    if (!mapRef.value) {
        return
    }

    try {
        loading.value = true
        error.value = null

        const sw = mapBounds.getSouthWest()
        const ne = mapBounds.getNorthEast()

        // Dynamic limit based on zoom level
        const limit = currentZoom >= 19 ? 10000 : currentZoom >= 18 ? 5000 : 2000

        // Fetch trees within viewport bounds using the api service
        const data = await api.getTrees({
            min_lat: sw.lat,
            max_lat: ne.lat,
            min_lon: sw.lng,
            max_lon: ne.lng,
            limit: limit,
        })

        // Warn if hitting limit
        if (data.length >= limit) {
            console.warn(`Loaded maximum ${data.length} trees. Zoom in further to see more.`)
        }

        trees.value = data
        loading.value = false
    } catch (e) {
        error.value = e instanceof Error ? e.message : 'Failed to fetch trees'
        console.error('Error fetching trees:', e)
        loading.value = false
    }
}

const onMapReady = (map: LeafletMap) => {
    mapRef.value = map

    // Fetch trees for initial viewport
    const initialBounds = map.getBounds()
    fetchTreesInBounds(initialBounds, map.getZoom())
}

// Watch for map movements with debouncing
watch([bounds, zoom], () => {
    if (!mapRef.value || !bounds.value) return

    // Clear existing timeout
    if (fetchTimeout) {
        clearTimeout(fetchTimeout)
    }

    // Debounce the fetch
    fetchTimeout = setTimeout(() => {
        if (bounds.value) {
            fetchTreesInBounds(bounds.value, zoom.value)
        }
    }, FETCH_DEBOUNCE_MS)
})
</script>

<template>
    <div class="map-container">
        <div v-if="loading" class="loading">Loading trees...</div>
        <div v-if="error" class="error">Error: {{ error }}</div>
        <div v-if="!loading && zoom < 17" class="zoom-prompt">
            Zoom in to level 17 or higher to see trees
        </div>
        <div v-if="!loading && zoom >= 17 && trees.length === 0" class="info">
            No trees found in this area
        </div>
        <div v-if="!loading && zoom >= 17 && trees.length > 0" class="info">
            Showing {{ trees.length }} trees (zoom {{ zoom }})
        </div>
        <l-map
            v-model:zoom="zoom"
            v-model:center="center"
            v-model:bounds="bounds"
            :use-global-leaflet="false"
            class="map"
            :min-zoom="5"
            :max-zoom="18"
            @ready="onMapReady"
        >
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
            <l-marker
                v-for="tree in trees"
                :key="tree.id"
                :lat-lng="[tree.latitude, tree.longitude]"
            >
                <l-popup>
                    <div class="tree-popup">
                        <strong>Tree ID:</strong> {{ tree.id }}<br />
                        <strong>Location:</strong> {{ tree.latitude.toFixed(6) }}, {{ tree.longitude.toFixed(6) }}<br />
                        <strong>Source:</strong> {{ tree.source_file }}<br />
                        <strong>Bounding Box:</strong><br />
                        &nbsp;&nbsp;xmin: {{ tree.bbox_xmin }}, ymin: {{ tree.bbox_ymin }}<br />
                        &nbsp;&nbsp;xmax: {{ tree.bbox_xmax }}, ymax: {{ tree.bbox_ymax }}
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
.error,
.zoom-prompt,
.info {
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

.info {
    background: #e7f3ff;
    color: #0066cc;
}

:deep(.tree-popup) {
    font-size: 14px;
    line-height: 1.5;
}
</style>
