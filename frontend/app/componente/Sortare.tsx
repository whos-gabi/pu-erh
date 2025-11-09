"use client";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, Filter, LayoutGrid } from "lucide-react";
import Link from "next/link";

type Types = {
  totalCount: number;
  tabel: string;
  id: string;
  selectedSort: string;
  setSelectedSort: React.Dispatch<React.SetStateAction<string>>;
  dateFromPathname: any;
};
const sortOptions = ["Populare", "Pret crescator", "Pret descrescator", "Noi"];

export default function Sortare({
  selectedSort,
  setSelectedSort,
  totalCount,
  tabel,
  id,
  dateFromPathname,
}: Types) {
  const [isSaved, setIsSaved] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    console.log(totalCount);
  }, [totalCount]);

  const categories = [
    {
      label: "Meeting Room",
      link: `/dashboard/meetingRoom1/${dateFromPathname}`,
    },
    {
      label: "Beer Point",
      link: `/dashboard/beerPointArea/${dateFromPathname}`,
    },
    {
      label: "Training Room 1",
      link: `/dashboard/meetingLarge1/${dateFromPathname}`,
    },
    {
      label: "Training Room 2",
      link: `/dashboard/meetingLarge2/${dateFromPathname}`,
    },
    { label: "Useri", link: `/produse/useri` },
  ];
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className="w-full flex flex-wrap items-center justify-between lg:px-[50px]">
      <div className="w-full">
        <h1 className="text-2xl font-bold">Cereri</h1>
        <div className="flex justify-between items-center text-sm py-2">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              {totalCount} rezultate
            </span>
            <div
              className="flex items-center gap-2 group cursor-pointer"
              onClick={() => setIsSaved((prev) => !prev)}
            ></div>
          </div>
          <div className="flex items-center gap-2 relative whitespace-nowrap">
            <div className="relative" ref={dropdownRef}>
              {isOpen && (
                <ul className="absolute right-0 bg-white border shadow-lg rounded-md mt-2 z-[6]">
                  {sortOptions.map((option) => (
                    <li
                      key={option}
                      onClick={() => {
                        setSelectedSort(option);
                        setIsOpen(false);
                      }}
                      className={`px-4 py-2 text-sm cursor-pointer hover:bg-gray-100 ${
                        selectedSort === option ? "font-semibold" : ""
                      }`}
                    >
                      {option}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <button className="border p-2 rounded-full bg-gray-100 hover:bg-gray-200">
              <LayoutGrid size={14} />
            </button>
          </div>
        </div>
      </div>
      <div className="flex gap-2 sm:mt-0 overflow-x-auto flex-nowrap scrollbar-hide pb-3">
        <button className="px-3 py-1 rounded-full text-sm border bg-gray-100 hover:bg-gray-200 whitespace-nowrap">
          <Filter size={14} />
        </button>
        {categories.map((filter, i) => (
          <Link key={i} href={filter.link}>
            <button
              className={`px-3 py-1 rounded-full text-sm border whitespace-nowrap ${
                id && filter.label.toLowerCase() === id
                  ? "bg-gray-800 text-white"
                  : "bg-gray-100 hover:bg-gray-200"
              }
                  ${i !== categories.length - 1 ? "" : "mr-3"}
              `}
            >
              {filter.label}
            </button>
          </Link>
        ))}
      </div>
    </div>
  );
}
