// Copyright (c) ipylab contributors
// Distributed under the terms of the Modified BSD License.
import { Signal } from '@lumino/signaling';

/**
 *Returns a nested object relative to `base`.
 * @param base The starting object.
 * @param dottedname The dotted path to the object.
 * @returns
 */

export function getNestedObject({
  base,
  dottedname,
  nullIfMissing = false
}: {
  base: object;
  dottedname: string;
  nullIfMissing?: boolean;
}): any {
  let obj: object = base;
  let dottedname_ = '';
  const parts = dottedname.split('.');
  let attr = '';
  for (let i = 0; i < parts.length; i++) {
    attr = parts[i];
    if (attr in obj) {
      obj = obj[attr as keyof typeof obj];
      dottedname_ = !dottedname_ ? attr : `${dottedname_}.${attr}`;
    } else {
      break;
    }
  }
  if (dottedname_ !== dottedname) {
    if (nullIfMissing) {
      return null;
    }
    throw new Error(`Failed to get the object for dottedname='${dottedname}'`);
  }
  return obj;
}

/**
 * Set a nested property relative to the base
 * @param base The object
 * @param dottedname The dotted path of the property to set
 * @param value The value to set as the property
 */
export function setNestedProperty(
  base: object,
  dottedname: string,
  value: any
) {
  const obj = getNestedObject({
    base: base,
    dottedname: dottedname.split('.').slice(0, -1).join('.')
  });
  obj[dottedname.split('.').slice(-1)[0]] = value;
}

/**
 * Convert a string definition of a function to a function object.
 * @param code The function as a string: eg. 'function (a, b) { return a + b; }'
 * @returns
 */
export function toFunction(code: string) {
  return new Function('return ' + code)();
}

/**
 * Provide an object detailing objects in obj.
 *
 * omitHidden: Will omit properties starting with '_'
 *
 * @param obj Any object.
 * @returns
 */
export function findAllProperties({
  obj,
  items = [],
  type = '',
  depth = 1,
  omitHidden = false
}: {
  obj: any;
  items?: Array<string>;
  type?: string;
  depth?: number;
  omitHidden?: boolean;
}): Array<string> {
  if (!obj || depth === 0) {
    return [...new Set(items)];
  }

  const props = Object.getOwnPropertyNames(obj).filter(value =>
    omitHidden ? value.slice(0, 1) !== '_' : true
  );
  return findAllProperties({
    obj: Object.getPrototypeOf(obj),
    items: [...items, ...props],
    type,
    depth: depth - 1,
    omitHidden: omitHidden
  });
}

/**
 * Returns a mapping of types and names for obj.
 * @param obj Any object
 * @returns
 */
export function listProperties({
  obj,
  type = '',
  depth = 1,
  omitHidden = false
}: {
  obj: any;
  type?: string;
  depth?: number;
  omitHidden?: boolean;
}): any {
  const out: any = {};
  for (const name of findAllProperties({
    obj,
    items: [],
    type,
    depth,
    omitHidden
  })) {
    const obj_ = obj[name];
    let type_: string = typeof obj_;
    let val: any = name;
    switch (type_) {
      case 'string':
      case 'number':
      case 'bigint':
      case 'boolean':
        out[name] = obj_;
        break;
      case 'undefined':
        out[name] = null;
      case 'object':
        if (obj_ instanceof Promise) {
          type_ = 'Promise';
          break;
        } else if (obj_ instanceof Signal) {
          type_ = 'Signal';
        }
        if (depth > 1) {
          val = {};
          val[name] = listProperties({ obj: obj_, type, depth: 1, omitHidden });
        }
      default:
        if (!out[`<${type_}s>`]) {
          out[`<${type_}s>`] = [val];
        } else {
          out[`<${type_}s>`].push(val);
          out[`<${type_}s>`] = out[`<${type_}s>`].sort();
        }
    }
  }
  // Sort alphabetically
  return Object.fromEntries(Object.entries(out).sort());
}
