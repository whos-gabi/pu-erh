"use client";

import { useEffect, useState } from "react";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import Tabele from "../componente/Tabele";
import Sortare from "../componente/Sortare";
import axiosInstance from "../componente/axiosInstance";
import { getSession } from "next-auth/react";
import axios from "axios";
import { useParams, useRouter } from "next/navigation";

export default function Page() {
  const [selectedSort, setSelectedSort] = useState<string>("");
  const router = useRouter();
  const params = useParams();
  const urlDateParam = params?.date;
  const urlDate = Array.isArray(urlDateParam) ? urlDateParam[0] : urlDateParam;

  // Parse string to Date, fallback to today
  const initialDate = urlDate ? new Date(urlDate) : new Date();

  const [date, setDate] = useState<Date>(initialDate);

  const formatDateForUrl = (date?: Date) => {
    if (!date) return "";
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, "0");
    const dd = String(date.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  };

  const handleDateChange = (d: Date | undefined) => {
    if (!d) return;
    setDate(d);
    console.log("bro");
    const formatted = formatDateForUrl(d); // use correct format for URL
    router.push(`/dashboard/meeting-room/${formatted}`);
  };

  const prevDay = () => {
    if (!date) return;
    console.log("--suka");
    const newDate = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate() - 1
    );
    setDate(newDate);
    router.push(`/dashboard/meeting-room/${formatDateForUrl(newDate)}`);
  };

  const nextDay = () => {
    if (!date) return;
    const newDate = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate() + 1
    );
    setDate(newDate);
    router.push(`/dashboard/meeting-room/${formatDateForUrl(newDate)}`);
  };

  useEffect(() => {
    async function getRequests() {
      const session = await getSession();
      const token = session?.user?.token;
      if (!token) return console.error("No token available");

      try {
        const res = await axios.get("/api/requests", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        console.log(res.data);
      } catch (err) {
        console.error(err);
      }
    }
    getRequests();
  }, []);

  const formatDate = (date?: Date) => {
    if (!date) return "Select Date";

    const day = date.getDate();
    const monthNames = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    const month = monthNames[date.getMonth()];
    const year = date.getFullYear();

    return `${day} ${month} ${year}`;
  };

  return (
    <div className="flex items-center h-screen flex-col">
      <div className="flex space-x-2">
        {/* Left arrow */}
        <Button
          variant="ghost"
          className="bg-transparent p-2 hover:bg-gray-100"
          onClick={prevDay}
        >
          {"<"}
        </Button>

        {/* Middle button opens popover calendar */}
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              className="bg-transparent px-4 py-2 border rounded-md hover:bg-gray-100"
            >
              {formatDate(date)}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar
              mode="single"
              selected={date}
              onSelect={handleDateChange}
              className="rounded-lg border [--cell-size:--spacing(11)] md:[--cell-size:--spacing(12)]"
            />
          </PopoverContent>
        </Popover>

        {/* Right arrow */}
        <Button
          variant="ghost"
          className="bg-transparent p-2 hover:bg-gray-100"
          onClick={nextDay}
        >
          {">"}
        </Button>
      </div>
      <Sortare
        totalCount={123}
        tabel="requests"
        id="meetingroom"
        selectedSort={selectedSort}
        setSelectedSort={setSelectedSort}
        dateFromPathname={formatDateForUrl(date)}
      />
      <Tabele dat={[]} />
    </div>
  );
}
