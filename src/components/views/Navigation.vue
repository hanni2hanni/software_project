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
        :highlighted-item="highlightedIndex"
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
import { mapGetters } from 'vuex'
import { watch } from 'vue'

export default {
  name: 'Navigation',
  data () {
    return {
      map: null, // 地图实例
      marker: null, // 当前标记点
      searchQuery: '', // 搜索框内容
      center: [116.397428, 39.90923], // 默认地图中心点
      AMap: null, // 用于存储 AMap 实例
      highlightedIndex: -1, // 当前高亮的建议项索引
      suggestions: [], // 存储搜索建议
      audio: null // 用于播放音频
    }
  },
  computed: {
    ...mapGetters(['recognitionData']) // 从 Vuex 中获取识别数据
  },
  mounted () {
    this.initMap() // 初始化地图
    this.playAudio(); // 播放音频

    // 监视 recognitionData.voice 的变化
    watch(
      () => this.recognitionData && this.recognitionData.voice,
      (newVoice) => {
        const invalidVoices = ["监听指令...", "识别失败..."];
        if (newVoice && !invalidVoices.includes(newVoice)) {
          this.searchQuery = newVoice; // 将有效的语音结果放入搜索框
        }
      }
    );

    // 监视 headpose 和 gaze 的变化
    watch(
      () => ({
        headpose: this.recognitionData && this.recognitionData.headpose,
        gaze: this.recognitionData && this.recognitionData.gaze
      }),
      ({ headpose, gaze }) => {
        if (gaze === '向下看') {
          this.switchSuggestions(); // 切换推荐框选项
        } else if (headpose === '点头') {
          this.performMapSearch(); // 执行地图搜索
        }
      }
    )
  },
  beforeDestroy () {
    if (this.map) {
      this.map.destroy() // 销毁地图实例
    }
  },
  methods: {
    // 播放音频
    playAudio() {
      this.audio = new Audio(require('@/assets/navigation.wav')); // 加载音频文件
      this.audio.play().catch(error => {
        console.error('Error playing audio:', error);
      });
    },

    // 初始化地图
    async initMap () {
      window._AMapSecurityConfig = {
        securityJsCode: '0079d087436433aedd5e5d1d40c36add'
      }

      this.AMap = await AMapLoader.load({
        key: '421d9632fe6cac6c95418e8717f99608',
        version: '2.0',
        plugins: ['AMap.Marker', 'AMap.ToolBar', 'AMap.Scale', 'AMap.Autocomplete', 'AMap.PlaceSearch']
      })

      // 创建地图实例
      this.map = new this.AMap.Map('map-container', {
        viewMode: '2D',
        center: this.center,
        zoom: 11
      })

      // 添加工具条和比例尺
      this.map.addControl(new this.AMap.ToolBar())
      this.map.addControl(new this.AMap.Scale())

      // 初始化标记点
      this.marker = new this.AMap.Marker({
        position: this.center,
        title: '当前位置'
      })
      this.map.add(this.marker)
    },

    // 切换推荐框选项
    switchSuggestions() {
      this.fetchSuggestions(this.searchQuery, (suggestions) => {
        this.suggestions = suggestions; // 保存当前建议
        if (suggestions.length > 0) {
          this.highlightedIndex = (this.highlightedIndex + 1) % suggestions.length; // 切换高亮选项
          this.searchQuery = suggestions[this.highlightedIndex].value; // 更新搜索框内容为当前高亮项
        }
      });
    },

    // 执行地图搜索
    performMapSearch() {
      if (this.highlightedIndex >= 0 && this.suggestions.length > 0) {
        const selectedSuggestion = this.suggestions[this.highlightedIndex];
        this.handleSelect(selectedSuggestion); // 选择当前高亮的建议
      }
    },

    // 搜索建议
    fetchSuggestions(queryString, callback) {
      console.log('Searching for:', queryString)
      if (!queryString) {
        callback([]);
        return;
      }

      const placeSearch = new this.AMap.PlaceSearch({
        city: '全国' // 可以根据需要指定城市
      });

      placeSearch.search(queryString, (status, result) => {
        console.log('Search status:', status);
        console.log('Search result:', result);
        if (status === 'complete' && result.info === 'OK') {
          const suggestions = result.poiList.pois.map(poi => ({
            value: poi.name,
            address: poi.address,
            location: poi.location
          }));
          callback(suggestions);
        } else {
          console.error('Error fetching suggestions:', result);
          callback([]);
        }
      });
    },

    // 选择地址后更新地图
    handleSelect(item) {
      console.log('Selected item:', item);
      if (item.location) {
        const location = item.location;
        let lng, lat;

        if (typeof location === 'string') {
          [lng, lat] = location.split(',').map(Number);
        } else if (location && typeof location === 'object') {
          lng = location.lng || location[0];
          lat = location.lat || location[1];
        }

        this.center = [lng, lat];
        this.map.setCenter(this.center);
        this.marker.setPosition(this.center);
      } else {
        console.error('Selected item does not have location:', item);
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
