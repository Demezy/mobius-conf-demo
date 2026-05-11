<script setup lang="ts">
import Feed from "./views/Feed.vue";
</script>

<template>
  <div class="wrap">
    <header>
      <h1>mobius</h1>
      <p>claude code session feed</p>
    </header>
    <Feed />
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #0f1115;
  color: #d8dee9;
}
.wrap {
  max-width: 980px;
  margin: 0 auto;
  padding: 24px;
}
header h1 {
  margin: 0;
  font-size: 22px;
}
header p {
  margin: 4px 0 16px;
  color: #7a8597;
  font-size: 13px;
}
</style>
