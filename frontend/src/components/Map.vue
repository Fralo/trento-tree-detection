<script setup lang="ts">
import { ref, onMounted, watch, shallowRef } from 'vue'
import { LMap, LWmsTileLayer } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import L, { type LatLngBounds, type Map as LeafletMap } from 'leaflet'
import 'leaflet.markercluster'

interface Tree {
    id: number
    latitude: number
    longitude: number
}

const trees = ref<Tree[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const bounds = ref<LatLngBounds | null>(null)
const mapRef = shallowRef<LeafletMap | null>(null)
const markerClusterGroup = shallowRef<L.MarkerClusterGroup | null>(null)

// Florence coordinates
const center = ref<[number, number]>([43.7696, 11.2558])
const zoom = ref(13)

let fetchTimeout: ReturnType<typeof setTimeout> | null = null
const FETCH_DEBOUNCE_MS = 500

const fetchTreesInBounds = async (mapBounds: LatLngBounds, currentZoom: number) => {
    // Progressive zoom levels - require higher zoom for more trees
    const minZoomForTrees = 17 // Increased from 15

    if (currentZoom < minZoomForTrees) {
        // Clear markers when zoomed out
        if (markerClusterGroup.value && mapRef.value) {
            markerClusterGroup.value.clearLayers()
            trees.value = []
        }
        return
    }

    // Don't fetch if marker cluster group isn't ready
    if (!markerClusterGroup.value || !mapRef.value) {
        return
    }

    try {
        loading.value = true
        error.value = null

        const sw = mapBounds.getSouthWest()
        const ne = mapBounds.getNorthEast()

        // Dynamic limit based on zoom level
        // Zoom 17: 2000 trees, Zoom 18: 5000 trees, Zoom 19+: 10000 trees
        const limit = currentZoom >= 19 ? 10000 : currentZoom >= 18 ? 5000 : 2000

        // Fetch trees within viewport bounds
        const params = new URLSearchParams({
            min_lat: sw.lat.toString(),
            max_lat: ne.lat.toString(),
            min_lon: sw.lng.toString(),
            max_lon: ne.lng.toString(),
            limit: limit.toString(),
        })

        const response = await fetch(`http://localhost:8000/trees?${params}`)
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()

        // Warn if hitting limit
        if (data.length >= limit) {
            console.warn(`Loaded maximum ${data.length} trees. Zoom in further to see more.`)
        }

        // Clear existing markers safely
        if (markerClusterGroup.value && mapRef.value) {
            markerClusterGroup.value.clearLayers()
        }

        // Add markers in batches to avoid blocking
        if (markerClusterGroup.value && mapRef.value && data.length > 0) {
            const BATCH_SIZE = 1000
            let processed = 0

            const addBatch = () => {
                const batch = data.slice(processed, processed + BATCH_SIZE)
                const markers = batch.map((tree: Tree) => {
                    const marker = L.marker([tree.latitude, tree.longitude])
                    marker.bindPopup(`
            <div class="tree-popup">
              <strong>Tree ID:</strong> ${tree.id}<br />
              <strong>Location:</strong> ${tree.latitude.toFixed(6)}, ${tree.longitude.toFixed(6)}
            </div>
          `)
                    return marker
                })

                if (markerClusterGroup.value) {
                    markerClusterGroup.value.addLayers(markers)
                }

                processed += BATCH_SIZE

                if (processed < data.length) {
                    // Process next batch
                    setTimeout(addBatch, 50)
                } else {
                    console.log(
                        `Loaded ${data.length} trees in viewport (zoom level ${currentZoom})`,
                    )
                    loading.value = false
                }
            }

            addBatch()
        } else {
            loading.value = false
        }

        trees.value = data
    } catch (e) {
        error.value = e instanceof Error ? e.message : 'Failed to fetch trees'
        console.error('Error fetching trees:', e)
        loading.value = false
    }
}

const onMapReady = (map: LeafletMap) => {
    mapRef.value = map

    // Create marker cluster group
    markerClusterGroup.value = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        chunkedLoading: true,
        chunkInterval: 200,
        chunkDelay: 50,
    })

    map.addLayer(markerClusterGroup.value)

    // Fetch trees for initial viewport
    const initialBounds = map.getBounds()
    fetchTreesInBounds(initialBounds, map.getZoom())
}

// Watch for map movements with debouncing
watch([bounds, zoom], () => {
    if (!mapRef.value || !bounds.value || !markerClusterGroup.value) return

    // Clear existing timeout
    if (fetchTimeout) {
        clearTimeout(fetchTimeout)
    }

    // Debounce the fetch
    fetchTimeout = setTimeout(() => {
        if (bounds.value && markerClusterGroup.value) {
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
            :max-zoom="20"
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

/* Customize marker cluster appearance */
:deep(.marker-cluster-small) {
    background-color: rgba(181, 226, 140, 0.6);
}

:deep(.marker-cluster-small div) {
    background-color: rgba(110, 204, 57, 0.6);
}

:deep(.marker-cluster-medium) {
    background-color: rgba(241, 211, 87, 0.6);
}

:deep(.marker-cluster-medium div) {
    background-color: rgba(240, 194, 12, 0.6);
}

:deep(.marker-cluster-large) {
    background-color: rgba(253, 156, 115, 0.6);
}

:deep(.marker-cluster-large div) {
    background-color: rgba(241, 128, 23, 0.6);
}
</style>
