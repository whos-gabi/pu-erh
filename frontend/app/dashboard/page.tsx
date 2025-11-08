"use client";

import * as React from "react";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import Tabele from "../componente/Tabele";
import Sortare from "../componente/Sortare";

export default function Page() {
  const [date, setDate] = React.useState<Date | undefined>(
    new Date(2025, 5, 12)
  );
  const [selectedSort, setSelectedSort] = React.useState<string>("");

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
      <Tabele
        dat={[
          {
            id: 1,
            created_at: "2025-11-08T10:30:00Z",
            name: "John Doe",
            email: "john@example.com",
            telefon: "+40712345678",
            status: "pending",
            cart: [
              {
                class: "ceai",
                model_id: "M001",
                item_id: "I001",
                pret: 45,
                quantity: 2,
              },
              {
                class: "ceainic",
                model_id: "M002",
                item_id: "I002",
                pret: 120,
                quantity: 1,
              },
            ],
          },
          {
            id: 2,
            created_at: "2025-11-07T15:15:00Z",
            name: "Alice Smith",
            email: "alice@example.com",
            telefon: "+40798765432",
            status: "done",
            cart: [
              {
                class: "set",
                model_id: "M003",
                item_id: "I003",
                pret: 250,
                quantity: 1,
              },
            ],
          },
          {
            id: 3,
            created_at: "2025-11-06T18:45:00Z",
            name: "Bob Johnson",
            email: "bob@example.com",
            telefon: "+40711223344",
            status: "declined",
            cart: [
              {
                class: "ceai",
                model_id: "M004",
                item_id: "I004",
                pret: 60,
                quantity: 3,
              },
            ],
          },
        ]}
      />
    </div>
  );
}
