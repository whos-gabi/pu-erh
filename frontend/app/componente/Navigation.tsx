import Link from "next/link";
import React, { MouseEventHandler } from "react";
import Image from "next/image";

export default function Navigation() {
  return (
    <nav>
      <div className="fixed z-10 w-full bg-black text-white">
        <div className="flex justify-between">
          <div>
            <Link className="w-full" href="/">
              <div className="p-5">Pu erh</div>
            </Link>
          </div>
          <div className="flex">
            <Link className="w-full" href="/">
              <div className="p-5">Admin</div>
            </Link>
            <Link className="w-full" href="/">
              <div className="p-5">Login</div>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
