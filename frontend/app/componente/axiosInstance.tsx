// lib/axios.ts
import axios from "axios";

const axiosInstance = axios.create({
  baseURL: "https://api.desepticon.qzz.io",
});

export default axiosInstance;
