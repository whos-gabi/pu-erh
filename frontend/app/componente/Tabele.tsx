"use client";

import React, { useEffect, useState } from "react";

type RowData = {
  id: number;
  user: string;
  roomCode: string;
  status: "WAITING" | "APPROVED" | "DECLINED";
  start_date: string;
  end_date: string;
  created_at: string;
  status_changed_at: string;
  decided_by: string;
  note: string;
};

type Props = {
  dat: RowData[];
};

export default function Tabele({ dat }: Props) {
  const [data, setData] = useState<RowData[]>(dat);
  useEffect(() => {
    setData(dat);
  }, [dat]);

  async function handleStatusChange(id: number, newStatus: string) {
    setData((prevData) =>
      prevData.map((row) =>
        row.id === id ? { ...row, status: newStatus as RowData["status"] } : row
      )
    );

    // Example backend update if needed:
    // await fetch(`/api/requests/${id}`, {
    //   method: "PATCH",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify({ status: newStatus }),
    // });
  }

  const formatDate = (date: string) => {
    const d = new Date(date);
    return d.toLocaleString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
    });
  };

  return (
    <div className="">
      <div className="overflow-x-auto bg-gray-100 rounded-lg shadow-md">
        <table className="w-full text-sm text-left text-gray-600">
          <thead className="bg-gray-200 text-gray-800">
            <tr>
              {["ID", "User", "Room", "Status", "Start Date", "End Date"].map(
                (col, index) => (
                  <th
                    key={index}
                    className="px-4 py-3 text-sm font-semibold uppercase tracking-wider"
                  >
                    {col}
                  </th>
                )
              )}
            </tr>
          </thead>

          <tbody>
            {data
              .slice()
              .reverse()
              .map((row, index) => (
                <tr
                  key={row.id}
                  className={`${
                    index % 2 === 0 ? "bg-gray-50" : "bg-white"
                  } hover:bg-gray-100 transition duration-150 ease-in-out`}
                >
                  <td className="px-4 py-3">{row.id}</td>
                  <td className="px-4 py-3">{row.user}</td>
                  <td className="px-4 py-3">
                    <p className="font-medium">{row.roomCode}</p>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={row.status}
                      onChange={(e) =>
                        handleStatusChange(row.id, e.target.value)
                      }
                      className={`px-2 py-1 rounded-full text-xs font-medium appearance-none flex justify-center ${
                        row.status === "APPROVED"
                          ? "bg-green-200 text-green-800"
                          : row.status === "WAITING"
                          ? "bg-yellow-200 text-yellow-800"
                          : "bg-red-200 text-red-800"
                      }`}
                    >
                      <option value="APPROVED">Approved</option>
                      <option value="DECLINED">Declined</option>
                      <option value="WAITING">Waiting</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">{formatDate(row.start_date)}</td>
                  <td className="px-4 py-3">{formatDate(row.end_date)}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
