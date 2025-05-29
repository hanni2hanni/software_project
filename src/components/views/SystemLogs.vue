<template>
  <div class="logs-container">
    <h1>系统运行日志</h1>

    <div class="log-table-container">
      <table class="log-table">
        <thead>
          <tr>
            <th>时间戳</th>
            <th>用户名</th>
            <th>模式</th>
            <th>动作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(log, index) in logs" :key="index">
            <td>{{ log.Timestamp }}</td>
            <td>{{ log.Username }}</td>
            <td>{{ log.Mode }}</td>
            <td>{{ log.Action }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="!logs.length" class="no-data">暂无日志数据: {{ errorMessage }}</p>
    </div>
    <div class="back-link-container">
      <router-link to="/admin" class="back-link">返回上一页</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SystemLogs',
  data() {
    return {
      logs: [],
      errorMessage: '',
    };
  },
  async mounted() {
    try {
      const response = await fetch('http://localhost:5000/api/logs');
      if (!response.ok) {
        throw new Error(`HTTP 错误: ${response.status} ${response.statusText}`);
      }
      const csvData = await response.text();
      if (!csvData.trim()) {
        throw new Error('日志数据为空');
      }
      this.parseCSV(csvData);
    } catch (error) {
      console.error('获取日志失败:', error);
      this.errorMessage = error.message;
      this.logs = [];
    }
  },
  methods: {
    parseCSV(csv) {
      const lines = csv.trim().split('\n');
      if (lines.length < 1) {
        throw new Error('CSV 数据无效');
      }

      const headers = lines[0].split(',').map(header => header.trim());
      if (headers.length < 4 || headers[0] !== 'Timestamp') {
        throw new Error('CSV 标题格式错误');
      }

      this.logs = lines.slice(1).map(line => {
        const values = line.split(',').map(val => val.trim());
        return {
          Timestamp: values[0] || '',
          Username: values[1] || '',
          Mode: values[2] || '',
          Action: values[3] || ''
        };
      });
    },
  },
};
</script>

<style scoped>
.logs-container {
  text-align: center;
  padding: 20px;
  color: #ecf0f1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  background-color: transparent;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  margin: 0;
  font-size: 24px;
}

.back-link-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;  /* 居中对齐 */
  width: 100%;
  padding-left: 0; /* 去掉多余的左内边距 */
}


.back-link {
  display: inline-block;
  padding: 10px 15px;
  color: #ecf0f1;
  background-color: #3498db;
  border: 1px solid #60aade;
  border-radius: 5px;
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.2s, color 0.3s;
}

.back-link:hover {
  background-color: #60aade;
  color: #fff;
  transform: scale(1.05);
}

.log-table-container {
  margin-top: 20px;
  background-color: rgba(52, 152, 219, 0.1);
  border: 2px solid #92cdf7;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
  max-height: 400px;
  overflow-y: auto;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  color: #ecf0f1;
}

.log-table th,
.log-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.log-table th {
  background-color: rgba(41, 128, 185, 0.4);
  position: sticky;
  top: 0;
  z-index: 1;
}

.log-table tr:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.no-data {
  text-align: center;
  color: #b0bec5;
  font-style: italic;
  padding: 20px;
}
</style>
