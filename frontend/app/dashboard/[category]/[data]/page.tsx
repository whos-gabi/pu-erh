"use client";

import { useEffect, useState } from "react";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import Tabele from "../../../componente/Tabele";
import Sortare from "../../../componente/Sortare";
import axiosInstance from "../../../componente/axiosInstance";
import { getSession } from "next-auth/react";
import axios from "axios";

type Props = {
  data: string;
  category: string;
};

export default function Page({
  params,
}: {
  params: { category: string; data: string };
}) {
  const [date, setDate] = useState<Date | undefined>(new Date(2025, 5, 12));
  const [selectedSort, setSelectedSort] = useState<string>("");

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

  const prevDay = () => {
    if (date)
      setDate(
        new Date(date.getFullYear(), date.getMonth(), date.getDate() - 1)
      );
  };

  const nextDay = () => {
    if (date)
      setDate(
        new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1)
      );
  };

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
              onSelect={(d) => setDate(d)}
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
        totalCount={123} // number of results
        tabel="bijuterii" // table or category
        id="inele" // current selected category
        selectedSort={selectedSort}
        setSelectedSort={setSelectedSort}
      />
      <Tabele dat={[]} />
    </div>
  );
}
