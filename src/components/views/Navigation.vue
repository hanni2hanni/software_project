<template>
  <div class="navigation">
    <h1>地图导航</h1>
    
    <!-- 地址输入框 -->
    <div class="search-container">
      <el-autocomplete
        class="address-input"
        v-model="searchQuery"
        :fetch-suggestions="fetchSuggestions"
        placeholder="输入地址进行搜索"
        @select="handleSelect"
        clearable
      >
        <template #item="{ item }">
          <div>
            <strong>{{ item.value }}</strong>
            <span>{{ item.address }}</span>
          </div>
        </template>
      </el-autocomplete>
    </div>

    <!-- 地图容器 -->
    <div id="map-container" class="map-container"></div>

    <!-- 返回按钮 -->
    <div class="back-link-container">
      <router-link to="/driver" class="back-link">返回驾驶员页面</router-link>
    </div>
  </div>
</template>

<script>
import AMapLoader from '@amap/amap-jsapi-loader'

export default {
  name: 'Navigation',
  data () {
    return {
      map: null,          // 地图实例
      marker: null,       // 当前标记点
      searchQuery: '',    // 搜索框内容
      center: [116.397428, 39.90923] // 默认地图中心点
    }
  },
  mounted () {
    this.initMap() // 初始化地图
  },
  beforeDestroy () {
    if (this.map) {
      this.map.destroy() // 销毁地图实例
    }
  },
  methods: {
    // 初始化地图
    async initMap () {
      window._AMapSecurityConfig = {
        securityJsCode: '0079d087436433aedd5e5d1d40c36add'
      }
      
      const AMap = await AMapLoader.load({
        key: '421d9632fe6cac6c95418e8717f99608',
        version: '2.0',
        plugins: ['AMap.Marker', 'AMap.ToolBar', 'AMap.Scale', 'AMap.Autocomplete', 'AMap.PlaceSearch']
      })

      // 创建地图实例
      this.map = new AMap.Map('map-container', {
        viewMode: "2D",
        center: this.center,
        zoom: 11
      })

      // 添加工具条和比例尺
      this.map.addControl(new AMap.ToolBar())
      this.map.addControl(new AMap.Scale())

      // 初始化标记点
      this.marker = new AMap.Marker({
        position: this.center,
        title: '当前位置'
      })
      this.map.add(this.marker)
    },

    // 搜索建议
    fetchSuggestions (queryString, callback) {
      console.log('Searching for:', queryString)
      if (!queryString) {
        callback([])
        return
      }

      const placeSearch = new AMap.PlaceSearch({
        city: '全国' // 可以根据需要指定城市
      })

      placeSearch.search(queryString, (status, result) => {
        console.log('Search status:', status)
        console.log('Search result:', result)
        if (status === 'complete' && result.info === 'OK') {
          // 处理数据格式，确保返回的每个对象都有一个 value 属性
          const suggestions = result.poiList.pois.map(poi => ({
            value: poi.name,
            address: poi.address,
            location: poi.location
          }))
          callback(suggestions)
        } else {
          console.error('Error fetching suggestions:', result)
          callback([])
        }
      })
    },

    // 选择地址后更新地图
    handleSelect (item) {
      console.log('Selected item:', item)
      if (item.location) {
        // 确保 location 是一个字符串，处理不同格式
        const location = item.location
        let lng, lat

        if (typeof location === 'string') {
          [lng, lat] = location.split(',').map(Number)
        } else if (location && typeof location === 'object') {
          lng = location.lng || location[0] // 根据 API 返回的数据格式
          lat = location.lat || location[1]
        }

        this.center = [lng, lat]

        this.map.setCenter(this.center)
        this.marker.setPosition(this.center)
      } else {
        console.error('Selected item does not have location:', item)
      }
    }
  }
}
</script>

<style scoped>
.navigation {
  text-align: center;
  padding: 20px;
  color: #ecf0f1;
  background-color: transparent;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

h1 {
  margin: 0;
  margin-bottom: 20px;
}

.search-container {
  width: 100%;
  max-width: 600px;
  margin: 0 auto 20px;
}

.address-input {
  width: 100%;
}

.map-container {
  width: 100%;
  height: 480px; /* 设置地图容器高度 */
  border: 1px solid #ccc;
  margin-bottom: 20px;
}

.back-link-container {
  margin-top: 20px;
}

.back-link {
  display: inline-block;
  padding: 10px 15px;
  color: #ecf0f1;
  text-decoration: none;
  border: 1px solid #60aade;
  border-radius: 5px;
  transition: background-color 0.3s, color 0.3s;
}

.back-link:hover {
  background-color: #60aade;
  color: #fff;
}
</style>
