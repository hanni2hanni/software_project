<template>
  <div class="home">
    <h1>车载多模态智能交互系统</h1>
    <p>欢迎使用我们的智能交互系统。请根据需要选择相应的功能。</p>
    <ul>
      <li>✓ 语音控制</li>
      <li>✓ 手势交互</li>
      <li>✓ 视觉交互</li>
      <li>✓ 系统管理</li>
    </ul>
  </div>
</template>

<script>
export default {
  name: 'Home',
};
</script>

<style scoped>
.home {
  text-align: center;
}

h1 {
  font-size: 2.5em; /* 标题大小 */
  color: #eef7fe; /* 标题颜色 */
}

p {
  font-size: 1.2em; /* 段落文字大小 */
  color: #eef7fe; /* 段落文字颜色 */
}

ul {
  list-style-type: none; /* 去掉列表标记 */
  padding: 0; /* 去掉内边距 */
}

li {
  font-size: 1.1em; /* 列表项大小 */
  color: #eef7fe; /* 列表项颜色 */
}

li:not(:last-child) {
  margin-bottom: 10px; /* 列表项间距 */
}
</style>
