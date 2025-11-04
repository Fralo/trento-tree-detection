import type { Tree } from '@/types/tree'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface GetTreesParams {
  min_lat?: number
  max_lat?: number
  min_lon?: number
  max_lon?: number
  limit?: number
}

export const api = {
  async getTrees(params?: GetTreesParams): Promise<Tree[]> {
    const queryParams = new URLSearchParams()
    
    if (params) {
      if (params.min_lat !== undefined) queryParams.append('min_lat', params.min_lat.toString())
      if (params.max_lat !== undefined) queryParams.append('max_lat', params.max_lat.toString())
      if (params.min_lon !== undefined) queryParams.append('min_lon', params.min_lon.toString())
      if (params.max_lon !== undefined) queryParams.append('max_lon', params.max_lon.toString())
      if (params.limit !== undefined) queryParams.append('limit', params.limit.toString())
    }
    
    const url = `${API_BASE_URL}/trees${queryParams.toString() ? '?' + queryParams.toString() : ''}`
    
    try {
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch trees: ${response.statusText}`)
      }
      
      const data: Tree[] = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching trees:', error)
      throw error
    }
  }
}
