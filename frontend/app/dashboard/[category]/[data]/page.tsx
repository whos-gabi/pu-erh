"use client";

import { useEffect, useState } from "react";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";

import { getSession } from "next-auth/react";
import axios from "axios";
import { useParams, usePathname, useRouter } from "next/navigation";
import Sortare from "@/app/componente/Sortare";
import Tabele from "@/app/componente/Tabele";

export default function Page() {
  const router = useRouter();
  const params = useParams();
  const urlDateParam = params?.date;
  const urlDate = Array.isArray(urlDateParam) ? urlDateParam[0] : urlDateParam;
  console.log("Extracted URL date:", urlDate);

  const [date, setDate] = useState<Date>();
  const [data, setData] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedSort, setSelectedSort] = useState<string>("");
  const pathname = usePathname();
  console.log("Full pathname:", pathname);

  // Example: if your URL is /dashboard/meeting-room/2025-11-09
  const pathSegments = pathname.split("/");
  const dateFromPathname = pathSegments[pathSegments.length - 1];
  console.log("Date extracted from pathname:", dateFromPathname);

  // Format date to YYYY-MM-DD for URL
  const formatDateForUrl = (d: Date) => {
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  };
  useEffect(() => {
    if (dateFromPathname) {
      setDate(new Date(dateFromPathname));
    }
  }, [dateFromPathname]);

  // Helper to navigate to new date
  const navigateToDate = (d: Date) => {
    setDate(d);
    const formatted = formatDateForUrl(d);
    router.push(`/dashboard/meetingRoom1/${formatted}`);
  };

  // Previous / Next day handlers
  const prevDay = () =>
    navigateToDate(
      new Date(date.getFullYear(), date.getMonth(), date.getDate() - 1)
    );
  const nextDay = () =>
    navigateToDate(
      new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1)
    );

  const handleDateChange = (d: Date | undefined) => {
    if (!d) return;
    navigateToDate(d);
  };

  // Fetch requests once
  useEffect(() => {
    async function getRequests() {
      const session = await getSession();
      const token = session?.user?.token;
      if (!token) return console.error("No token available");

      try {
        console.log(params);
        const room = params.category;
        const date = dateFromPathname;

        const url = `/api/requests?roomCode=${room}&date=${date}`;

        const res = await fetch(url, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            accept: "application/json",
          },
        });
        const data = await res.json();

        // Now you can access your array
        setData(data.requests);
        console.log("Full response:", data);
        setTotalCount(data.total);
      } catch (err) {
        console.error(err);
      }
    }
    getRequests();
  }, []);

  // Format date nicely for display (e.g., 22 November 2025)
  const formatDateForDisplay = (d?: Date) => {
    if (!d) return "Select Date";
    const day = d.getDate();
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
    const month = monthNames[d.getMonth()];
    const year = d.getFullYear();
    return `${day} ${month} ${year}`;
  };

  return (
    <div className="flex items-center h-screen flex-col space-y-4">
      <div className="flex space-x-2 items-center">
        {/* Left arrow */}
        <Button variant="ghost" className="p-2" onClick={prevDay}>
          {"<"}
        </Button>

        {/* Calendar popover */}
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="ghost" className="px-4 py-2 border rounded-md">
              {formatDateForDisplay(date)}
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
        <Button variant="ghost" className="p-2" onClick={nextDay}>
          {">"}
        </Button>
      </div>

      {/* Sorting */}
      <Sortare
        dateFromPathname={dateFromPathname}
        totalCount={totalCount} // example
        tabel="bijuterii"
        id="inele"
        selectedSort={selectedSort}
        setSelectedSort={setSelectedSort}
      />

      {/* Table */}
      <Tabele dat={data} />
    </div>
  );
}
